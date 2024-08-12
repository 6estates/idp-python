# coding: utf-8
# Created by hujian on 2024/8/5 16:50
#
import time
import requests
from sixe_idp.api import Task, IDPException, TaskResult, IDPConfigurationException


# class CustomerType(Enum):
#     """Customer type:
#         1 means Individual/Retail or Consumer Loan,
#         2 means Company/Business or Productive Loan.
#     """
#     INDIVIDUAL_RETAIL = 1
#     COMPANY_BUSINESS = 2

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
        return self.response.reason

    @property
    def zip_content_bytes(self):
        """
        List of :class:`TaskResultField <TaskResultField>` object
        """
        return self.response.content

    def write_content_to_zip(self,zip_file_path):
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
        self.url_get = "https://idp" + region + \
                       ".6estates.com/customer/extraction/faas/analysis/export/"

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
        print(data)
        r = requests.post(self.url_post, headers=headers, files=files, data=data)
        if r.ok:
            return Task(r.json())
        raise IDPException(r.json()['message'])

    def run_simple_task(self, files, customerType, countryId, informationType, poll_interval=3, timeout=600)->TaskResult:
        """
        Simply upload a faas extraction task
        Only for test this async function, cannot be used in real production
        :param files: files
        :type files: list

        :param customerType: customerType
        :type customerType: str

        :param countryId: countryId
        :type countryId: str

        :param informationType: informationType
        :type informationType: str

        :param poll_interval: poll_interval
        :type poll_interval: int

        :param timeout: timeout
        :type timeout: int
        """
        start = time.time()
        task = self.create(files=files, customerType=customerType, countryId=countryId, informationType=informationType)
        task_result = self.result(task_id=task.task_id)

        while (task_result.status == 'Doing' or task_result.status == 'Init'):
            if time.time() - start > timeout:
                raise IDPException(f'Task timeout exceeded: {timeout}')
            time.sleep(poll_interval)
            task_result = self.result(task_id=task.task_id)

        if task_result.status == 'Done':
            return task_result

        return task_result
    def result(self, task_id=None) -> FaasTaskResult:
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

        # if r.ok:
        #     return FaasTaskResult(r)
        # raise IDPException(r.json()['message'])
        return FaasTaskResult(r)

class FaasClient(object):
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
        self.extraction_task = FaasExtractionTaskClient(token=token, region=region, isOauth=self.isOauth)
        """
            An :class:`ExtractionTaskClient <ExtractionTaskClient>` object
        """

