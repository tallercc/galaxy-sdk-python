import string
from unicodedata import category
from emq.common.ttypes import GalaxyEmqServiceException
from emq.range.constants import GALAXY_EMQ_QUEUE_DELAY_SECONDS_MINIMAL, GALAXY_EMQ_QUEUE_DELAY_SECONDS_MAXIMAL, \
  GALAXY_EMQ_QUEUE_INVISIBILITY_SECONDS_MAXIMAL, GALAXY_EMQ_QUEUE_INVISIBILITY_SECONDS_MINIMAL, \
  GALAXY_EMQ_QUEUE_RECEIVE_WAIT_SECONDS_MINIMAL, GALAXY_EMQ_QUEUE_RECEIVE_WAIT_SECONDS_MAXIMAL, \
  GALAXY_EMQ_QUEUE_RECEIVE_NUMBER_MAXIMAL, GALAXY_EMQ_QUEUE_RECEIVE_NUMBER_MINIMAL, \
  GALAXY_EMQ_QUEUE_RETENTION_SECONDS_MINIMAL, GALAXY_EMQ_QUEUE_RETENTION_SECONDS_MAXIMAL, \
  GALAXY_EMQ_QUEUE_MAX_MESSAGE_BYTES_MINIMAL, GALAXY_EMQ_QUEUE_MAX_MESSAGE_BYTES_MAXIMAL, \
  GALAXY_EMQ_QUEUE_PARTITION_NUMBER_MINIMAL, GALAXY_EMQ_QUEUE_PARTITION_NUMBER_MAXIMAL, \
  GALAXY_EMQ_MESSAGE_DELAY_SECONDS_MAXIMAL, GALAXY_EMQ_MESSAGE_DELAY_SECONDS_MINIMAL, \
  GALAXY_EMQ_MESSAGE_INVISIBILITY_SECONDS_MAXIMAL, GALAXY_EMQ_MESSAGE_INVISIBILITY_SECONDS_MINIMAL
from emq.message.ttypes import SendMessageRequest, ReceiveMessageRequest, ChangeMessageVisibilityRequest, \
  DeleteMessageRequest, SendMessageBatchRequest, SendMessageBatchRequestEntry, ChangeMessageVisibilityBatchRequestEntry, \
  ChangeMessageVisibilityBatchRequest, DeleteMessageBatchRequest
from emq.queue.ttypes import CreateQueueRequest, ListQueueRequest, SetQueueAttributesRequest, SetPermissionRequest, \
  RevokePermissionRequest, QueryPermissionForIdRequest


class RequestChecker(object):
  def __init__(self, args=tuple()):
    self.__args = args

  def check_arg(self):
    if len(self.__args) > 1:
      errMsg = "Unknown request"
      raise GalaxyEmqServiceException(errMsg=errMsg)
    else:
      self.check_request_params(self.__args[0])

  def check_request_params(self, request):
    if isinstance(request, ListQueueRequest):
      self.validate_queue_prefix(request.queueNamePrefix)
    elif isinstance(request, CreateQueueRequest):
      self.validate_queue_name(request.queueName, False)
      self.validate_queue_attribute(request.queueAttribute)
    elif isinstance(request, SetQueueAttributesRequest):
      self.validate_queue_name(request.queueName)
      self.validate_queue_attribute(request.queueAttribute)
    elif isinstance(request, SetPermissionRequest):
      self.validate_queue_name(request.queueName)
      self.validate_not_none(request.developerId, "developerId")
      self.validate_not_none(request.permission, "permission")
    elif isinstance(request, RevokePermissionRequest):
      self.validate_queue_name(request.queueName)
      self.validate_not_none(request.developerId, "developerId")
    elif isinstance(request, QueryPermissionForIdRequest):
      self.validate_queue_name(request.queueName)
      self.validate_not_none(request.developerId, "developerId")
    elif isinstance(request, SendMessageRequest):
      self.validate_queue_name(request.queueName)
      self.validate_not_none(request.messageBody, "messageBody")
    elif isinstance(request, ReceiveMessageRequest):
      self.validate_queue_name(request.queueName)
      if request.maxReceiveMessageNumber is not None:
        self.validate_receiveMessageMaximumNumber(request.maxReceiveMessageNumber)
      if request.maxReceiveMessageWaitSeconds is not None:
        self.validate_receiveMessageWaitSeconds(request.maxReceiveMessageWaitSeconds)
    elif isinstance(request, ChangeMessageVisibilityRequest):
      self.validate_queue_name(request.queueName)
      if request.invisibilitySeconds is not None:
        self.validate_invisibilitySeconds(request.invisibilitySeconds)
      self.validate_not_none(request.receiptHandle, "receiptHandle")
      self.validate_not_empty(request.receiptHandle, "receiptHandle")
    elif isinstance(request, DeleteMessageRequest):
      self.validate_queue_name(request.queueName)
      self.validate_not_none(request.receiptHandle, "receiptHandle")
      self.validate_not_empty(request.receiptHandle, "receiptHandle")
    elif isinstance(request, SendMessageBatchRequest):
      self.validate_queue_name(request.queueName)
      sendMessageBatchRequestEntryList = request.sendMessageBatchRequestEntryList
      self.validate_not_empty(sendMessageBatchRequestEntryList, "sendMessageBatchRequestEntryList")
      entry_id_list = []
      for k in sendMessageBatchRequestEntryList:
        self.validate_not_none(k.entryId, "entryId")
        self.validate_not_empty(k.entryId, "entryId")
        entry_id_list.append(k.entryId)
        self.check_send_entry(k)
      self.check_list_duplicate(entry_id_list, "entryId")
    elif isinstance(request, ChangeMessageVisibilityBatchRequest):
      self.validate_queue_name(request.queueName)
      changeMessageVisibilityBatchRequestEntryList = request.changeMessageVisibilityRequestEntryList
      self.validate_not_empty(changeMessageVisibilityBatchRequestEntryList, "changeMessageVisibilityBatchRequestEntryList")
      receipt_handle_list = []
      for k in changeMessageVisibilityBatchRequestEntryList:
        self.validate_not_none(k.receiptHandle, "receiptHandle")
        self.validate_not_empty(k.receiptHandle, "receiptHandle")
        receipt_handle_list.append(k.receiptHandle)
        self.check_change_entry(k)
      self.check_list_duplicate(receipt_handle_list, "receiptHandle")
    elif isinstance(request, DeleteMessageBatchRequest):
      self.validate_queue_name(request.queueName)
      deleteMessageBatchRequestEntryList = request.deleteMessageBatchRequestEntryList
      self.validate_not_empty(deleteMessageBatchRequestEntryList, "deleteMessageBatchRequestEntryList")
      receipt_handle_list = []
      for k in deleteMessageBatchRequestEntryList:
        self.validate_not_none(k.receiptHandle, "receiptHandle")
        self.validate_not_empty(k.receiptHandle, "receiptHandle")
        receipt_handle_list.append(k.receiptHandle)
      self.check_list_duplicate(receipt_handle_list, "receiptHandle")
    else:
      self.validate_queue_name(request.queueName)

  def check_send_entry(self, send_entry):
    self.validate_not_none(send_entry.messageBody, "messageBody")
    if send_entry.delaySeconds is not None:
      self.validate_delaySeconds(send_entry.delaySeconds)
    if send_entry.invisibilitySeconds is not None:
      self.validate_invisibilitySeconds(send_entry.invisibilitySeconds)

  def check_change_entry(self, change_entry):
    self.validate_not_none(change_entry.invisibilitySeconds, "invisibilitySeconds")
    self.validate_invisibilitySeconds(change_entry.invisibilitySeconds)

  def check_list_duplicate(self, l, name):
    if len(l) != len({}.fromkeys(l).keys()):
      raise GalaxyEmqServiceException(errMsg="Bad request, %s shouldn't be duplicate." % name)

  def validate_queue_name(self, queue_name, allow_slash=True, is_prefix=False, param_name="queue name"):
    chars = list(queue_name)
    if queue_name == "" or queue_name is None:
      raise GalaxyEmqServiceException(errMsg="Bad request, %s shouldn't be empty." % param_name)
    for c in chars:
      if not self.isJavaIdentifierPart(c) or (not allow_slash and c == "/"):
        raise GalaxyEmqServiceException(errMsg="Bad request, Invalid characters in %s." % param_name)
    if allow_slash and len(queue_name.split("/")) != 2 and not is_prefix:
      raise GalaxyEmqServiceException(errMsg="Bad request, please check your '/' in %s." % param_name)
    if is_prefix and len(queue_name.split("/")) != 1 and len(queue_name.split("/")) != 2:
      raise GalaxyEmqServiceException(errMsg="Bad request, please check your '/' in %s." % param_name)

  @staticmethod
  def isJavaIdentifierPart(c):
    if c in string.ascii_letters:
      return True
    if c in string.digits:
      return True
    if c in string.punctuation:
      return True
    if category(unicode(c)) == 'Sc':
      return True
    if category(unicode(c)) == 'Mn':
      return True
    if category(unicode(c)) == 'N1':
      return True
    if category(unicode(c)) == 'Mc':
      return False
    return False

  def validate_queue_prefix(self, queue_prefix):
    self.validate_queue_name(queue_prefix, True, True, "queue name prefix")

  def validate_queue_attribute(self, queue_attribute):
    if not queue_attribute:
      return
    if queue_attribute.delaySeconds:
      self.validate_delaySeconds(queue_attribute.delaySeconds)
    if queue_attribute.invisibilitySeconds:
      self.validate_invisibilitySeconds(queue_attribute.invisibilitySeconds)
    if queue_attribute.receiveMessageWaitSeconds:
      self.validate_receiveMessageWaitSeconds(queue_attribute.receiveMessageWaitSeconds)
    if queue_attribute.receiveMessageMaximumNumber:
      self.validate_receiveMessageMaximumNumber(queue_attribute.receiveMessageMaximumNumber)
    if queue_attribute.messageRetentionSeconds:
      self.validate_messageRetentionSeconds(queue_attribute.messageRetentionSeconds)
    if queue_attribute.messageMaximumBytes:
      self.validate_messageMaximumBytes(queue_attribute.messageMaximumBytes)
    if queue_attribute.partitionNumber:
      self.validate_partitionNumber(queue_attribute.partitionNumber)

  def check_filed_range(self, value, low, high, name):
    if not isinstance(value, int):
      raise GalaxyEmqServiceException(errMsg="Bad request, wrong date type of %s!" % name)
    if value < low or value > high:
      raise GalaxyEmqServiceException(errMsg="Bad request, the attribute value of %s is out of range!" % name)

  def validate_delaySeconds(self, delaySeconds):
    self.check_filed_range(delaySeconds,
                           GALAXY_EMQ_QUEUE_DELAY_SECONDS_MINIMAL,
                           GALAXY_EMQ_QUEUE_DELAY_SECONDS_MAXIMAL,
                           "delaySeconds")

  def validate_invisibilitySeconds(self, invisibilitySeconds):
    self.check_filed_range(invisibilitySeconds,
                           GALAXY_EMQ_QUEUE_INVISIBILITY_SECONDS_MINIMAL,
                           GALAXY_EMQ_QUEUE_INVISIBILITY_SECONDS_MAXIMAL,
                           "invisibilitySeconds")

  def validate_receiveMessageWaitSeconds(self, receiveMessageWaitSeconds):
    self.check_filed_range(receiveMessageWaitSeconds,
                           GALAXY_EMQ_QUEUE_RECEIVE_WAIT_SECONDS_MINIMAL,
                           GALAXY_EMQ_QUEUE_RECEIVE_WAIT_SECONDS_MAXIMAL,
                           "receiveMessageWaitSeconds")

  def validate_receiveMessageMaximumNumber(self, receiveMessageMaximumNumber):
    self.check_filed_range(receiveMessageMaximumNumber,
                           GALAXY_EMQ_QUEUE_RECEIVE_NUMBER_MINIMAL,
                           GALAXY_EMQ_QUEUE_RECEIVE_NUMBER_MAXIMAL,
                           "receiveMessageMaximumNumber")

  def validate_messageRetentionSeconds(self, messageRetentionSeconds):
    self.check_filed_range(messageRetentionSeconds,
                           GALAXY_EMQ_QUEUE_RETENTION_SECONDS_MINIMAL,
                           GALAXY_EMQ_QUEUE_RETENTION_SECONDS_MAXIMAL,
                           "messageRetentionSeconds")

  def validate_messageMaximumBytes(self, messageMaximumBytes):
    self.check_filed_range(messageMaximumBytes,
                           GALAXY_EMQ_QUEUE_MAX_MESSAGE_BYTES_MINIMAL,
                           GALAXY_EMQ_QUEUE_MAX_MESSAGE_BYTES_MAXIMAL,
                           "messageMaximumBytes")

  def validate_partitionNumber(self, partitionNumber):
    self.check_filed_range(partitionNumber,
                           GALAXY_EMQ_QUEUE_PARTITION_NUMBER_MINIMAL,
                           GALAXY_EMQ_QUEUE_PARTITION_NUMBER_MAXIMAL,
                           "partitionNumber")

  def validate_messageDelaySeconds(self, messageDelaySeconds):
    self.check_filed_range(messageDelaySeconds,
                           GALAXY_EMQ_MESSAGE_DELAY_SECONDS_MINIMAL,
                           GALAXY_EMQ_MESSAGE_DELAY_SECONDS_MAXIMAL,
                           "messageDelaySeconds")

  def validate_messageInvisibilitySeconds(self, messageInvisibilitySeconds):
    self.check_filed_range(messageInvisibilitySeconds,
                           GALAXY_EMQ_MESSAGE_INVISIBILITY_SECONDS_MINIMAL,
                           GALAXY_EMQ_MESSAGE_INVISIBILITY_SECONDS_MAXIMAL,
                           "messageInvisibilitySeconds")

  def validate_not_none(self, param, name):
    if param is None:
      raise GalaxyEmqServiceException(errMsg="Bad request, the %s is required!" % name)

  def validate_not_empty(self, param, name):
    if not param:
        raise GalaxyEmqServiceException(errMsg="Bad request, the %s shouldn't be empty!" % name)
