import time
from enum import Enum

import requests


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
    npwp = 'NPWP'  # Nomor Pokok Wajib Pajak
    nric = 'NRIC'  # Singapore NRIC
    zhid = 'ZHID'  # China ID
    pp = 'PP'  # China Passport
    dos = 'DOS'  # Financial Statement	DOS
    bfp = 'BFP'  # ACRA BizFile	BFP
    bpkb = 'BPKB'  # Buku Pemilik Kendaraan Bermotor	BPKB
    kk = 'KK'  # Kartu Keluarga	KK
    crn = 'CRN'  # Credit Note	CRN
    dbn = 'DBN'  # Debit Note	DBN
    stnk = 'STNK'  # Surat Tanda Nomor Kendaraan	STNK
    cinq = 'CINQ'  # Product Inquiry	CINQ
    cd = 'CD'  # Company Deed	CD


class ExtractMode(Enum):
    Lite = 1
    Regular = 2
    Advance = 3


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
        return self.raw['data']['taskStatus']

    @property
    def fields(self):
        """
        List of :class:`TaskResultField <TaskResultField>` object
        """
        return [TaskResultField(x) for x in self.raw['data']['fields']]


class ExtractionTaskClient(object):
    def __init__(self, token=None, region=None, isOauth=False):
        """
        Initializes task extraction
        :param str token: Client's token
        :param str region: Region to make requests to, defaults to 'sea'
        :param bool isOauth: Oauth 2.0 flag
        """
        self.token = token
        self.region = region
        self.isOauth = isOauth
        # URL to upload file and get response
        if region == 'test':
            region = ''
        else:
            region = '-' + region
        self.url_post = "https://idp" + region + \
                        ".6estates.com/customer/extraction/fields/async"
        self.url_get = "https://idp" + region + \
                       ".6estates.com/customer/extraction/field/async/result/"

    def create(self, file=None, file_type=None, lang=None,
               customer=None, customer_param=None, callback=None,
               auto_callback=None, callback_mode=None, hitl=None, extractMode=None, includingFieldCodes=None, autoChecks=None, fileTypeFrom=None, remark=None) -> Task:
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
        :param extractMode: The mode of extraction. 1:Lite, 2:Regular, 3:Advance, 2 as Default.
        :param includingFieldCodes: the fieldCodes that needs to be included in the callback response. Default value is all fieldCodes.
            it is like str ['F_CBKS_1','F_CBKS_2'], all unfiltered fieldCodes as default.
        :param autoChecks: if return auth check content, 0 means NO return, 1 means return, 0 as default
        :param fileTypeFrom: 1 means ordinary using system defined file type, 2 means using user defined file type, 1 as default
        :param remark:
        """
        assert isinstance(file_type, FileType), "Invalid file type"
        # assert isinstance(extractMode, ExtractMode), "Invalid Extract Mode"
        if file is None:
            raise IDPException("File is required")

        if self.isOauth:
            headers = {"Authorization": self.token}
        else:
            headers = {"X-ACCESS-TOKEN": self.token}
        files = {"file": file}
        data = {'fileType': file_type.value, 'lang': lang, 'customer': customer,
                'customerParam': customer_param, 'callback': callback,
                'autoCallback': auto_callback, 'callbackMode': callback_mode,
                'hitl': hitl, 'ExtractMode': extractMode, 'includingFieldCodes': includingFieldCodes}
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
        if self.isOauth:
            headers = {"Authorization": self.token}
        else:
            headers = {"X-ACCESS-TOKEN": self.token}
        r = requests.get(self.url_get + str(task_id), headers=headers)

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

        while (task_result.status == 'Doing' or task_result.status == 'Init'):
            if time.time() - start > timeout:
                raise IDPException(f'Task timeout exceeded: {timeout}')
            time.sleep(poll_interval)
            task_result = self.result(task_id=task.task_id)

        if task_result.status == 'Done':
            return task_result

        return task_result


class OauthClient(object):
    def __init__(self, region=None):
        """
        Initializes the Oauth Client 

        :param region: IDP Region to make requests to, e.g. 'test'
        :type region: str
        :returns: :class:`OauthClient <OauthClient>`
        :rtype: sixe_idp.api.OauthClient
        """

        if region not in ['test', 'sea']:
            raise IDPConfigurationException(
                "Region is required and limited in ['test','sea']")
        self.region = region

        if region == 'test':
            region = '-onp'
        else:
            region = '-' + region
        self.url_post = "https://oauth" + region + \
                        ".6estates.com/oauth/token?grant_type=client_bind"

    def get_IDP_authorization(self, authorization=None):
        """
        :param authorization: Client's authorization
        :type authorization: str


        """
        if authorization is None:
            raise IDPConfigurationException('Authorization is required')
        self.authorization = authorization

        headers = {"Authorization": self.authorization}
        r = requests.post(self.url_post, headers=headers)

        if r.ok:
            if r.json()['data']['expired'] == False:
                return r.json()['data']['value']
            else:
                raise IDPException(
                    "This IDP Authorization is expired, please re-send the request to get new IDP Authorization. " +
                    r.json()['message'])

        raise IDPException(r.json()['message'])


class Client(object):
    def __init__(self, region=None, token=None, isOauth=False):
        """
        Initializes the IDP Client

        :param token: Client's token
        :type token: str
        :param region: IDP Region to make requests to, e.g. 'test'
        :param bool isOauth: Oauth 2.0 flag
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
        self.isOauth = isOauth
        self.extraction_task = ExtractionTaskClient(token=token, region=region, isOauth=self.isOauth)
        """
            An :class:`ExtractionTaskClient <ExtractionTaskClient>` object
        """
