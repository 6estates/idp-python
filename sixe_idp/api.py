import hashlib
import time
from enum import Enum

import requests


class ExtractMode(Enum):
    Lite = 1
    Regular = 2
    Advance = 3


def build_sha256_str(clientId, clientSecret, timestamp):
    """
    get the oauth signature through clientId,clientSecret and timestamp
    :param clientId: clientId
    :type clientId: str

    :param clientSecret: clientSecret
    :type clientSecret: str

    :param timestamp: timestamp
    :type timestamp: int
    """
    input_str = str(clientId) + str(clientSecret) + str(timestamp)
    sha256_hash = hashlib.sha256(input_str.encode('utf-8')).hexdigest()
    return sha256_hash


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
        self.url_post = f"https://oauth{region}.6estates.com/oauth/token?grant_type=client_bind"
        self.new_authorization_url = f"https://oauth{region}.6estates.com/api/token"
        self.clientId = None
        self.clientSecret = None

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

    def get_IDP_new_authorization(self, clientId=None, clientSecret=None):
        if clientId is None or clientSecret is None:
            raise IDPConfigurationException('clientId&clientSecret are required')
        self.clientId = clientId
        self.clientSecret = clientSecret

        headers = {"Content-Type": "application/json"}
        current_timestamp = int(time.time() * 1000)
        signature = build_sha256_str(self.clientId, self.clientSecret, current_timestamp)
        data = {
            "clientId": clientId,
            "timestamp": current_timestamp,
            "signature": signature
        }

        r = requests.post(self.new_authorization_url, headers=headers, json=data)
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
        self.headers = {"Authorization": self.token} if self.isOauth else {"X-ACCESS-TOKEN": self.token}

        self.extraction_task = ExtractionTaskClient(token=token, region=region, isOauth=self.isOauth)
        self.faas_extraction_task = FaasExtractionTaskClient(token=token, region=region, isOauth=self.isOauth)
        if region == 'test':
            url_region = ''
        else:
            url_region = '-' + region
        self.extraction_async_create_url = f"https://idp{url_region}.6estates.com/customer/extraction/fields/async"
        self.extraction_result_url = f"https://idp{url_region}.6estates.com/customer/extraction/field/async/result/"
        self.extraction_task_history_url = f"https://idp{url_region}.6estates.com/customer/extraction/history/list"
        self.extraction_task_add_hitl_url = f"https://idp{url_region}.6estates.com/customer/extraction/task/to_hitl"

        self.extraction_faas_create_url = f"https://idp{url_region}.6estates.com/customer/extraction/faas/analysis"
        self.extraction_faas_export_url = f"https://idp{url_region}.6estates.com/customer/extraction/faas/analysis/export/"
        self.extraction_faas_result_url = f"https://idp{url_region}.6estates.com/customer/extraction/faas/analysis/result/"

        self.extraction_doc_agent_create_url = f"https://idp{url_region}.6estates.com/customer/extraction/doc_agent/analysis"
        self.extraction_doc_agent_status_url = f"https://idp{url_region}.6estates.com/customer/extraction/doc_agent/status/"
        self.extraction_doc_agent_export_url = f"https://idp{url_region}.6estates.com/customer/extraction/doc_agent/analysis/export/"

    def extraction_async_create(self, file=None, file_type=None, fileTypeFrom=None,
                                lang=None,
                                customer=None, customer_param=None, callback=None,
                                auto_callback=None, callback_mode=None, hitl=None,
                                extractMode=None, includingFieldCodes=None,
                                autoChecks=None, remark=None):
        """
        :param file: Pdf/image file. Only one file is allowed to be uploaded each time
        :type file: file
        :param file_type: The str of the file type (e.g., CBKS), this could be CBKS,CINV those publick file type and can also be self-defined file type if fileTypeFrom is set to be 2
        :type file_type: str
        :param lang: English: EN, Default is EN
        :type lang: str
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
        if file is None:
            raise IDPException("File is required")
        if file_type is None:
            raise IDPException("file_type is required")

        files = {"file": file}
        data = {'fileType': file_type, 'lang': lang, 'customer': customer,
                'customerParam': customer_param, 'callback': callback,
                'autoCallback': auto_callback, 'callbackMode': callback_mode,
                'hitl': hitl, 'ExtractMode': extractMode, 'includingFieldCodes': includingFieldCodes,
                'autoChecks': autoChecks, 'fileTypeFrom': fileTypeFrom, 'remark': remark
                }
        trash_bin = []
        for key in data:
            if data[key] is None:
                trash_bin.append(key)
        for key in trash_bin:
            del data[key]
        r = requests.post(self.extraction_async_create_url, headers=self.headers,
                          files=files, data=data)
        if r.ok:
            return Task(r.json())
        raise IDPException(r.json()['message'])

    def extraction_result(self, task_id=None):
        """
        :param task_id: task_id
        :type task_id: int

        :returns: status and result of task
        :rtype: :class:`TaskResult <TaskResult>`

        """

        r = requests.get(self.extraction_result_url + str(task_id), headers=self.headers)
        if r.ok:
            return r.json()
        raise IDPException(r.json()['message'])

    def extraction_task_history(self, page=None, limit=None, sortColumn=None, sortOrder=None, status=None,
                                fileTypeCode=None,
                                source=None, edited=None, hitl=None, fileName=None, startCreateTime=None,
                                endCreateTime=None):
        """
        This function query the history tasks in the system
        page	Query page of list.	query	required	Integer
        limit	Query task size for a page.	query	required	Integer
        sortColumn	The column will sort by, support "id" and "create_time".
        If empty system will use "id" default.	query	optional	String
        sortOrder	The order type will sort by, support "ascending" and "descending", if empty system will use "descending" default.	query	required	String
        taskStatus	Filter task list by task status: 1 init, 2 doing, 3 done, 4 failed, 5 Invalid, 6 Unreadable. taskStatus is replaced by 'status'	query	optional	Integer
        status	Filter task list by task status: 0 Failed, 1 On Process, 2 Finished - Check Document Insight 3 Finished - No Issue, 4 Failed - Invalid document, 5 HITL Assignment, 6 Failed - Unreadable document.	query	optional	Integer
        fileTypeCode	Filter task list by file type code, for example: cbks, cinv.	query	optional	String
        source	Filter task list by task come form source: 1 web, 2 api.	query	optional	Integer
        edited	Filter task list by task edited or not: true or false.	query	optional	Boolean
        hitl	Filter task list by task use HITL or not : true or false.	query	optional	Boolean
        fileName	Filter task list by upload file name, support fuzzy query.	query	optional	String
        startCreateTime	Filter task list by task created time range start, format is "yyyy-MM-dd", will append "00:00:00.000" automatic.	query	optional	Integer
        endCreateTime	Filter task list by task created time range end, format is "yyyy-MM-dd", will append "23:59:59.999" automatic.	query	optional	Integer
        """
        if page is None:
            raise IDPException("page is required")
        if limit is None:
            raise IDPException("limit is required")
        data = {'page': page,
                'limit': limit,
                'sortColumn': sortColumn,
                'sortOrder': sortOrder,
                'status': status,
                'fileTypeCode': fileTypeCode,
                'source': source,
                'edited': edited,
                'hitl': hitl,
                'fileName': fileName,
                'startCreateTime': startCreateTime,
                'endCreateTime': endCreateTime}
        trash_bin = []
        for key in data:
            if data[key] is None:
                trash_bin.append(key)
        for key in trash_bin:
            del data[key]
        # print(data)
        r = requests.get(self.extraction_task_history_url, headers=self.headers, params=data)
        if r.ok:
            return r.json()
        else:
            raise IDPException(r.json()['message'])

    def extraction_task_add_hitl(self, applicationId, callback=None, autoCallback=None, callbackMode=None):
        """
        applicationId	The id of task which you submitted before.	RequestBody	Required	String
        callback	Same with the parameter when you submitted the file, if the task has no callback url or you want reset the callback url, you can set this parameter.	RequestBody	Optional	String
        autoCallback	Same with the parameter when you submitted the file, if you want change the exists value of task, you can set this parameter.	RequestBody	Optional	Boolean
        callbackMode	Same with the parameter when you submitted the file, If you want change the mode of task callback, you can set this parameter.
        mode 0: callback request only contains the task status.
        mode 1: callback request contains task status and extracted field results.
        mode 2: callback request contains task status, extracted fields results and pdf file.
        mode 3: callback request contains task status, extracted fields results,pdf file,export Excel file, export json file.	RequestBody	Optional	Integer
        """
        if applicationId is None:
            raise IDPException('applicationId is required')

        data = {'applicationId': applicationId,
                'callback': callback,
                'autoCallback': autoCallback,
                'callbackMode': callbackMode}
        trash_bin = []
        for key in data:
            if data[key] is None:
                trash_bin.append(key)
        for key in trash_bin:
            del data[key]
        # print(data)
        r = requests.post(self.extraction_task_add_hitl_url, headers=self.headers, json=data)
        if r.ok:
            return r.json()
        raise IDPException(r.json()['message'])

    def extraction_faas_create(self, files,
                              customerType: int,
                              countryId: str = None,
                              regionId: str = None,
                              informationType: int = None,
                              cifNumber: str = None,
                              borrowerName: str = None,
                              loanAmount: float = None,
                              applicationNumber: str = None,
                              applicationDate: str = None,
                              currency: str = None,
                              rateDateType: int = None,
                              rateFrom: int = None,
                              rateDate: str = None,
                              automatic: bool = True,
                              hitlType: int = 0,
                              industryType: str = None,
                              industryBiCode: str = None,
                              ebitdaRatio: str = None,
                              relatedParties: str = None,
                              supplierBuyer: str = None,
                              checkAccountStr: str = None,
                              callbackUrl: str = None,
                              autoCallback: bool = True,
                              callbackMode: int = 0):
        """
        Args:
            files (str): Support PDF/IMG/Zip file. Please make sure only pdf/image file in zip file.
            customerType (str): Customer type: 1 means Individual/Retail or Consumer Loan, 2 means Company/Business or Productive Loan.
            countryId (str, optional): Id of country. Defaults to None.
            regionId (str, optional): Id of region. Defaults to None.
            informationType (int, optional): Information type: 0 New Customer, 1 Existing Customer. Defaults to None.
            cifNumber (str, optional): A unique number that the banks assign to each customer. Defaults to None.
            borrowerName (str, optional): Borrower company name. Defaults to None.
            loanAmount (float, optional): A specific amount that borrowers apply for. Defaults to None.
            applicationNumber (str, optional): A unique number that the banks assign to each application. Defaults to None.
            applicationDate (str, optional): A specific date when the application submitted. Defaults to None.
            currency (str, optional): Which currency this insight case will be used. Defaults to None.
            rateDateType (int, optional): Which currency rate will be used. Defaults to None.
            rateFrom (int, optional): Which currency rate provider will be used. Defaults to None.
            rateDate (str, optional): Customized date for currency rate. Defaults to None.
            automatic (bool, optional): The insight will analysis by automatic. Defaults to True.
            hitlType (int, optional): Setting of Human in The Loop. Defaults to 0.
            industryType (str, optional): Which industry type this insight case related. Defaults to None.
            industryBiCode (str, optional): Which industry BI code this insight case related. Defaults to None.
            ebitdaRatio (str, optional): Customized ebitda ratio. Defaults to None.
            relatedParties (str, optional): Related party information. Defaults to None.
            supplierBuyer (str, optional): Supplier and Buyer information. Defaults to None.
            checkAccountStr (str, optional): Supplier and Buyer information. Defaults to None.
            callbackUrl (str, optional): A http(s) link for callback after completing the task. Defaults to None.
            autoCallback (bool, optional): Callback request will request automatic. Defaults to True.
            callbackMode (int, optional): Callback mode when the task finishes. Defaults to 0.

            For those params are not clearly defined, please refer to the API documentation. https://idp-sea.6estates.com/document
        """
        if files is None:
            raise IDPException("Files are required")

        data = {"customerType": customerType,
                "countryld": countryId,
                "regionld": regionId,
                "informationType": informationType,
                "cifNumber": cifNumber,
                "borrowerName": borrowerName,
                "loanAmount": loanAmount,
                "applicationNumber": applicationNumber,
                "applicationDate": applicationDate,
                "currency": currency,
                "rateDateType": rateDateType,
                "rateFrom": rateFrom,
                "rateDate": rateDate,
                "automatic": automatic,
                "hitlType": hitlType,
                "industryType": industryType,
                "industryBiCode": industryBiCode,
                "ebitdaRatio": ebitdaRatio,
                "relatedParties": relatedParties,
                "supplierBuyer": supplierBuyer,
                "checkAccountStr": checkAccountStr,
                "callbackUrl": callbackUrl,
                "autoCallback": autoCallback,
                "callbackMode": callbackMode
                }
        trash_bin = []
        for key in data:
            if data[key] is None:
                trash_bin.append(key)
        for key in trash_bin:
            del data[key]
        # print(data)
        r = requests.post(self.extraction_faas_create_url, headers=self.headers, files=files, data=data)
        if r.ok:
            return Task(r.json())
        raise IDPException(r.json()['message'])

    def extraction_faas_result(self, task_id=None):
        """
        :param task_id: task_id
        :type task_id: int

        :returns: status and result of task
        :rtype: :class:`TaskResult <TaskResult>`

        """
        r = requests.get(self.extraction_faas_result_url + str(task_id), headers=self.headers)
        return r.json()
        # return FaasTaskResult(r.json())

    def extraction_faas_export(self, task_id=None):
        """
        :param task_id: task_id
        :type task_id: int

        :returns: status and result of task
        :rtype: :class:`TaskResult <TaskResult>`

        """
        r = requests.get(self.extraction_faas_export_url + str(task_id), headers=self.headers)
        # you might need to read the r.content as a result zip file
        if 'errorCode' in r.text:
            raise IDPException(r.text)
        else:
            return r.content

    def extraction_doc_agent_create(self, flowCode: int,
                                    file,
                                    callback: str = None,
                                    autoCallback: bool = None,
                                    callbackMode: int = None,
                                    callbackQaCodes: str = None):
        """
        Args:
            flowCode (int): The code of task flow, please contact 6E admin to obtain the task flow code.
            file (str): Support PDF/IMG/Zip file. Please make sure only pdf/image file in zip file.
            callback (str, optional): A http(s) link for callback after completing the task.
                    If you need to use the callback parameter, please communicate with us if your callback system needs any authentication mechanism.
            autoCallback (bool, optional): Callback request will request automatic if autoCallback is true, otherwise, the user needs to manually trigger the callback.
                    Default value is true.
            callbackMode (int, optional): Callback mode when the task finishes.
                    mode 1: callback request contains task flow result file.
                    Default is 1.Later we will support more callback modes.
            callbackQaCodes (str, optional):Task flow Qa codes. When callbackMode == 1, if you want to pass only part of the task flow Qa result during the callback, you can control it through this parameter
            For those params are not clearly defined, please refer to the API documentation. https://idp-sea.6estates.com/document
        """
        if file is None:
            raise IDPException("File is required")
        if flowCode is None:
            raise IDPException("flowCode is required")
        data = {
            "flowCode": flowCode,
            "callback": callback,
            "autoCallback": autoCallback,
            "callbackMode": callbackMode,
            "callbackQaCodes": callbackQaCodes,
        }
        files = {"file": file}
        trash_bin = []
        for key in data:
            if data[key] is None:
                trash_bin.append(key)
        for key in trash_bin:
            del data[key]
        # print(data)
        r = requests.post(self.extraction_doc_agent_create_url, headers=self.headers, files=files, data=data)
        if r.ok:
            return Task(r.json())
        raise IDPException(r.json()['message'])

    def extraction_doc_agent_status(self, applicationId):
        """
            Get the status of a task.
        """
        if applicationId is None:
            raise IDPException("applicationId is required")
        r = requests.post(self.extraction_doc_agent_status_url + applicationId, headers=self.headers)
        if r.ok:
            return r.json()
        else:
            raise IDPException(r.json()['message'])

    def extraction_doc_agent_export(self, applicationId):
        """
            Get the result of a task.
        """
        if applicationId is None:
            raise IDPException("applicationId is required")
        r = requests.post(self.extraction_doc_agent_export_url + applicationId, headers=self.headers)
        if r.ok:
            return r.content
        else:
            raise IDPException(r.json()['message'])


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
               auto_callback=None, callback_mode=None, hitl=None, extractMode=ExtractMode.Regular, includingFieldCodes=None, autoChecks=None, fileTypeFrom=None, remark=None) -> Task:
        """
        :param file: Pdf/image file. Only one file is allowed to be uploaded each time
        :type file: file
        :param file_type: The str of the file type (e.g., CBKS), this could be CBKS,CINV those publick file type and can also be self-defined file type if fileTypeFrom is set to be 2
        :type file_type: str
        :param lang: English: EN, Default is EN
        :type lang: str
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
        # assert isinstance(file_type, FileType), "Invalid file type"
        assert isinstance(extractMode, ExtractMode), "Invalid Extract Mode"
        if file is None:
            raise IDPException("File is required")

        if self.isOauth:
            headers = {"Authorization": self.token}
        else:
            headers = {"X-ACCESS-TOKEN": self.token}
        files = {"file": file}
        data = {'fileType': file_type, 'lang': lang, 'customer': customer,
                'customerParam': customer_param, 'callback': callback,
                'autoCallback': auto_callback, 'callbackMode': callback_mode,
                'hitl': hitl, 'ExtractMode': extractMode.value, 'includingFieldCodes': includingFieldCodes,
                'autoChecks': autoChecks, 'fileTypeFrom': fileTypeFrom, 'remark': remark
                }
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

    # def run_simple_task(self, file=None, file_type=None, poll_interval=3, timeout=600):
    #     """
    #         Run simple extraction task
    #
    #         :param file: Pdf/image file. Only one file is allowed to be uploaded each time
    #         :type file: file
    #         :param file_type: The code of the file type (e.g., CBKS). Please see details of File Type Code.
    #         :type file_type: str
    #         :param poll_interval: Interval to poll the result from api, in seconds
    #         :type poll_interval: float
    #         :param timeout: Timeout in seconds
    #         :type timeout: float
    #     """
    #     start = time.time()
    #     task = self.create(file=file, file_type=file_type)
    #     task_result = self.result(task_id=task.task_id)
    #
    #     while (task_result.status == 'Doing' or task_result.status == 'Init'):
    #         if time.time() - start > timeout:
    #             raise IDPException(f'Task timeout exceeded: {timeout}')
    #         time.sleep(poll_interval)
    #         task_result = self.result(task_id=task.task_id)
    #
    #     if task_result.status == 'Done':
    #         return task_result
    #
    #     return task_result


class FaasTaskResult(object):
    def __init__(self, response):
        self.response = response

    @property
    def task_id(self):
        return self.response.url.split('/')[-1]

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
        return self.response.status_code

    @property
    def zip_content_bytes(self):
        """
        List of :class:`TaskResultField <TaskResultField>` object
        """
        return self.response.content

    def write_content_to_zip(self, zip_file_path):
        with open(zip_file_path, 'wb') as f:
            f.write(self.zip_content_bytes)
            f.close()
        return zip_file_path


class FaasExtractionTaskClient(object):
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
                        ".6estates.com/customer/extraction/faas/analysis"
        self.url_get_export = "https://idp" + region + \
                              ".6estates.com/customer/extraction/faas/analysis/export/"
        self.url_get_result = "https://idp" + region + \
                              ".6estates.com/customer/extraction/faas/analysis/result/"

    def create(self, files,
               customerType: int,
               countryId: str = None,
               regionId: str = None,
               informationType: int = None,
               cifNumber: str = None,
               borrowerName: str = None,
               loanAmount: float = None,
               applicationNumber: str = None,
               applicationDate: str = None,
               currency: str = None,
               rateDateType: int = None,
               rateFrom: int = None,
               rateDate: str = None,
               automatic: bool = True,
               hitlType: int = 0,
               industryType: str = None,
               industryBiCode: str = None,
               ebitdaRatio: str = None,
               relatedParties: str = None,
               supplierBuyer: str = None,
               checkAccountStr: str = None,
               callbackUrl: str = None,
               autoCallback: bool = True,
               callbackMode: int = 0) -> Task:
        """
        Args:
            files (str): Support PDF/IMG/Zip file. Please make sure only pdf/image file in zip file.
            customerType (str): Customer type: 1 means Individual/Retail or Consumer Loan, 2 means Company/Business or Productive Loan.
            countryId (str, optional): Id of country. Defaults to None.
            regionId (str, optional): Id of region. Defaults to None.
            informationType (int, optional): Information type: 0 New Customer, 1 Existing Customer. Defaults to None.
            cifNumber (str, optional): A unique number that the banks assign to each customer. Defaults to None.
            borrowerName (str, optional): Borrower company name. Defaults to None.
            loanAmount (float, optional): A specific amount that borrowers apply for. Defaults to None.
            applicationNumber (str, optional): A unique number that the banks assign to each application. Defaults to None.
            applicationDate (str, optional): A specific date when the application submitted. Defaults to None.
            currency (str, optional): Which currency this insight case will be used. Defaults to None.
            rateDateType (int, optional): Which currency rate will be used. Defaults to None.
            rateFrom (int, optional): Which currency rate provider will be used. Defaults to None.
            rateDate (str, optional): Customized date for currency rate. Defaults to None.
            automatic (bool, optional): The insight will analysis by automatic. Defaults to True.
            hitlType (int, optional): Setting of Human in The Loop. Defaults to 0.
            industryType (str, optional): Which industry type this insight case related. Defaults to None.
            industryBiCode (str, optional): Which industry BI code this insight case related. Defaults to None.
            ebitdaRatio (str, optional): Customized ebitda ratio. Defaults to None.
            relatedParties (str, optional): Related party information. Defaults to None.
            supplierBuyer (str, optional): Supplier and Buyer information. Defaults to None.
            checkAccountStr (str, optional): Supplier and Buyer information. Defaults to None.
            callbackUrl (str, optional): A http(s) link for callback after completing the task. Defaults to None.
            autoCallback (bool, optional): Callback request will request automatic. Defaults to True.
            callbackMode (int, optional): Callback mode when the task finishes. Defaults to 0.

            For those params are not clearly defined, please refer to the API documentation. https://idp-sea.6estates.com/document
        """
        if files is None:
            raise IDPException("Files are required")

        if self.isOauth:
            headers = {"Authorization": self.token}
        else:
            headers = {"X-ACCESS-TOKEN": self.token}
        data = {"customerType": customerType,
                "countryld": countryId,
                "regionld": regionId,
                "informationType": informationType,
                "cifNumber": cifNumber,
                "borrowerName": borrowerName,
                "loanAmount": loanAmount,
                "applicationNumber": applicationNumber,
                "applicationDate": applicationDate,
                "currency": currency,
                "rateDateType": rateDateType,
                "rateFrom": rateFrom,
                "rateDate": rateDate,
                "automatic": automatic,
                "hitlType": hitlType,
                "industryType": industryType,
                "industryBiCode": industryBiCode,
                "ebitdaRatio": ebitdaRatio,
                "relatedParties": relatedParties,
                "supplierBuyer": supplierBuyer,
                "checkAccountStr": checkAccountStr,
                "callbackUrl": callbackUrl,
                "autoCallback": autoCallback,
                "callbackMode": callbackMode
                }
        trash_bin = []
        for key in data:
            if data[key] is None:
                trash_bin.append(key)
        for key in trash_bin:
            del data[key]
        # print(data)
        r = requests.post(self.url_post, headers=headers, files=files, data=data)
        if r.ok:
            return Task(r.json())
        raise IDPException(r.json()['message'])

    # def run_simple_task(self, files, customerType, countryId, informationType, poll_interval=3,
    #                     timeout=600) -> TaskResult:
    #     """
    #     Simply upload a faas extraction task
    #     Only for test this async function, cannot be used in real production
    #     :param files: files
    #     :type files: list
    #
    #     :param customerType: customerType
    #     :type customerType: str
    #
    #     :param countryId: countryId
    #     :type countryId: str
    #
    #     :param informationType: informationType
    #     :type informationType: str
    #
    #     :param poll_interval: poll_interval
    #     :type poll_interval: int
    #
    #     :param timeout: timeout
    #     :type timeout: int
    #     """
    #     start = time.time()
    #     task = self.create(files=files, customerType=customerType, countryId=countryId, informationType=informationType)
    #     task_result = self.result(task_id=task.task_id)
    #
    #     while (task_result.status == 'Doing' or task_result.status == 'Init'):
    #         if time.time() - start > timeout:
    #             raise IDPException(f'Task timeout exceeded: {timeout}')
    #         time.sleep(poll_interval)
    #         task_result = self.result(task_id=task.task_id)
    #
    #     if task_result.status == 'Done':
    #         return task_result
    #
    #     return task_result

    def result(self, task_id=None):
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
        r = requests.get(self.url_get_result + str(task_id), headers=headers)
        return r.json()
        # return FaasTaskResult(r.json())

    def export(self, task_id=None):
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
        r = requests.get(self.url_get_export + str(task_id), headers=headers)
        # you might need to read the r.content as a result zip file
        if 'errorCode' in r.text:
            raise IDPException(r.text)
        else:
            return r.content

