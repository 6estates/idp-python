import time
import requests
from enum import Enum


class FileType(Enum):

    bank_statement = 'CBKS'
    invoice = 'CINV'
    cheque = 'CHQ'
    credit_bureau_singapore = 'CBS'
    receipt = 'RCPT'
    payslip = 'PS'
    packing_list = 'PL'
    bill_of_lading = 'BL'
    air_waybill = 'AWBL'
    kartu_tanda_penduduk = 'KTP'
    hong_kong_annual_return = 'HKAR'
    purchase_order = 'PO'
    delivery_order = 'DO'


class IDPException(Exception):
    """
        An IDP processing error occurred.
    """
    pass


class IDPConfigurationException(Exception):
    """
        An IDP configuration error occurred.
    """
    pass


class Task(object):
    """
        The :class:`Task <Task>` object, which contains a server's response to an IDP task creating request.
    """

    def __init__(self, raw=None):
        self.raw = raw

    @property
    def task_id(self):
        return self.raw['data']

class TaskResultField:
    def __init__(self, raw) -> None:
        self.raw = raw

    @property
    def field_code(self):
        """
        see `field_code <https://idp-sea.6estates.com/docs#/types/type_desc>`_
        """
        return self.raw['field_code']

    @property
    def field_name(self):
        """
        see `field_name <https://idp-sea.6estates.com/docs#/types/type_desc>`_
        """
        return self.raw['field_name']

    @property
    def value(self):
        return self.raw['value']

    @property
    def type(self):
        """
        see `type <https://idp-sea.6estates.com/docs#/format/format>`_
        """
        
        return self.raw['type']

    # @property
    # def extraction_confidence(self):
    #     return self.raw['extraction_confidence']

class TaskResult(object):
    def __init__(self, raw):
        self.raw = raw

    @property
    def status(self):
        """
        status of the task, which can be:

        - **Init** Task is created
        - **Doing** Task is being processed
        - **Done** Task result is avaiable
        - **Fail** An error occurred
        - **Invalid** Invalid document

        read `more <https://idp-sea.6estates.com/docs#/extract/extraction?id=_2135-response>`_
        """
        return self.raw['data']['status']

    @property
    def fields(self):
        """
        List of :class:`TaskResultField <TaskResultField>` object
        """
        return [TaskResultField(x) for x in self.raw['data']['fields']]

class ExtractionTaskClient(object):
    def __init__(self, token=None, region=None):
        """
        Initializes task extraction
        :param str token: Client's token
        :param str region: Region to make requests to, defaults to 'sea'
        """
        self.token = token
        self.region = region
        # URL to upload file and get response
        if region == 'test':
            region = ''
        else:
            region = '-'+region
        self.url_post = "https://idp"+region + \
            ".6estates.com/customer/extraction/fields/async"
        self.url_get = "https://idp"+region + \
            ".6estates.com/customer/extraction/field/async/result/"

    def create(self, file=None, file_type=None, lang=None,
               customer=None, customer_param=None, callback=None,
               auto_callback=None, callback_mode=None, hitl=None) -> Task:
        """
        :param lang: English: EN, Default is EN
        :type lang: str
        :param file: Pdf/image file. Only one file is allowed to be uploaded each time
        :type file: file
        :param file_type: The code of the file type (e.g., CBKS). Please see details of File Type Code.
        :type file_type: FileType
        :param customer: Enterprise/customer code (e.g., ABCD). a fixed value provided by 6E.
        :type customer: str
        :param customer_param: Any value in string specified by customer enterprise/customer. This value will return in callback request.
        :type customer_param: str
        :param callback: A http(s) link for callback after completing the task. If you need to use the callback parameter, please make sure that the callback url does not have any authentication.
        :type callback: str
        :param auto_callback: Callback request will request automatic if autoCallback is true, otherwise, the user needs to manually trigger the callback.Default value is true.
        :type auto_callback: bool
        :param callback_mode:  Callback mode when the task finishes.
            
            - `mode 0`: callback request only contains the task status.
            - `mode 1`: callback request contains task status and extracted field results.
            - `mode 2`: callback request contains task status, extracted fields results and pdf file. 
            
            Default is 0.
        :type callback_mode: int
        :param hitl: Enables the Human-In-The-Loop (HITL) service. If the value is true, the submitted task will be processed by AI + HITL. Otherwise, the task will be processed by AI only.
            Default value: false.
        :type hitl: bool
        """
        assert isinstance(file_type, FileType), "Invalid file type"
        if file is None:
            raise IDPException("File is required")

        headers = {"X-ACCESS-TOKEN": self.token}
        files = {"file": file}
        data = {'fileType': file_type.value, 'lang': lang, 'customer': customer,
                'customerParam': customer_param, 'callback': callback,
                'autoCallback': auto_callback, 'callbackMode': callback_mode,
                'hitl': hitl}
        trash_bin = []
        for key in data:
            if data[key] is None:
                trash_bin.append(key)
        for key in trash_bin:
            del data[key]
        r = requests.post(self.url_post, headers=headers,
                          files=files, data=data)
        if r.ok:
            return Task(r.json())
        raise IDPException(r.json()['message'])

    def result(self, task_id=None) -> TaskResult:
        """
        :param task_id: task_id
        :type task_id: int

        :returns: status and result of task
        :rtype: :class:`TaskResult <TaskResult>`

        """
        headers = {"X-ACCESS-TOKEN": self.token}
        r = requests.get(self.url_get+str(task_id), headers=headers)
        if r.ok:
            return TaskResult(r.json())
        raise IDPException(r.json()['message'])

    def run_simple_task(self, file=None, file_type=None, poll_interval=3, timeout=600):
        """
            Run simple extraction task 

            :param file: Pdf/image file. Only one file is allowed to be uploaded each time
            :type file: file
            :param file_type: The code of the file type (e.g., CBKS). Please see details of File Type Code.
            :type file_type: FileType
            :param poll_interval: Interval to poll the result from api, in seconds
            :type poll_interval: float
            :param timeout: Timeout in seconds
            :type timeout: float
        """
        start = time.time()
        task = self.create(file=file, file_type=file_type)
        task_result = self.result(task_id=task.task_id)
        while(task_result.status=='Doing' or task_result.status=='Init'):
            if time.time() - start > timeout:
                raise IDPException(f'Task timeout exceeded: {timeout}')
            time.sleep(poll_interval)
            task_result = self.result(task_id=task.task_id)
            
        if task_result.status == 'Done':
            return task_result

        return task_result


class Client(object):
    def __init__(self, region=None, token=None):
        """
        Initializes the IDP Client

        :param token: Client's token
        :type token: str
        :param region: IDP Region to make requests to, e.g. 'test'
        :type token: str
        :returns: :class:`Client <Client>`
        :rtype: sixe_idp.api.Client
        """
        if token is None:
            raise IDPConfigurationException('Token is required')
        if region not in ['test', 'sea']:
            raise IDPConfigurationException(
                "Region is required and limited in ['test','sea']")
        self.region = region
        self.token = token

        self.extraction_task = ExtractionTaskClient(token=token, region=region)
        """
            An :class:`ExtractionTaskClient <ExtractionTaskClient>` object
        """