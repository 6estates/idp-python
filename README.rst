6Estates idp-python
==============
A Python SDK for communicating with the 6Estates Intelligent Document Processing(IDP) Platform.

We did some api upgrade, simplified the api using and return, gives you much more freedom.
We recommend to use client.extraction_async_create() to replace the client.extraction_task.create()
and client.extraction_result() to replace client.extraction_task.result()

Documentation
-----------------

The documentation for the 6Estates IDP API can be found via https://idp-sea.6estates.com/docs

The Python library documentation can be found via https://idp-sdk-doc.6estates.com


Setup
-----------------

.. code-block:: bash

    pip install 6estates-idp


Usage 
============ 
1. Initialize the 6Estates IDP Client 
---------------------------------------------------------------------

6E API Authorization based on oauth 2.0

.. code-block:: python

    import time
    from sixe_idp.api import Client, OauthClient
    # NOTE: the OauthClient and Client initialization is different from the previous versions
    # For possible change, full web url needs to be provided
    client_id = 'your client id found on web'
    client_secret = 'your client secret found on web'
    oauth_client = OauthClient(client_id=client_id, client_secret=client_secret)
    client = Client(http_host='https://idp-sea.6estates.com', oauth_client=oauth_client)
    # Also added a way to refresh token, default is every 90 minutes, every func has already updated the token internally
    client.refresh_token(refresh_interval=90*60)
2. Asynchronous Information Extraction API
--------------------------------------------------------------------

2.1 Asynchronous Submit File for Fields Extraction
~~~~~~~~~~~~
.. code-block:: python

    # We have multiple ways to create the IDP task, and we only show CBKS file type as a demo
    task = client.extraction_async_create(file=open("/your/file/path/upload/idp/test_file.pdf", "rb"),file_type='CBKS')
    print(task.task_id)


2.2 To Get Fields Extraction Result By TaskId
~~~~~~~~~~~~
.. code-block:: python

    application_id = '12345'
    task_result = client.extraction_result(application_id=application_id)  # try to fetch the result
    print(task_result)


2.3 Query History Task List
~~~~~~~~~~~~
.. code-block:: python

    history = client.extraction_task_history(page=1,limit=10)
    print(history)

2.4 Add Task to HITL
~~~~~~~~~~~~
.. code-block:: python

    application_id = 'your application_id/task_id'
    add_hitl = client.extraction_task_add_hitl(applicationId=application_id)

2.5 Sample of create a simple extraction job and fetch result
~~~~~~~~~~~~

.. code-block:: python

    # This is only a simple demo, showing how to create an extraction task and fetch the result
    import time
    from sixe_idp.api import Client, OauthClient, IDPException
    def run_simple_task(client, file_path=None, file_type=None, poll_interval=30, timeout=600):
        """
            Run simple extraction task

            :param file: Pdf/image file. Only one file is allowed to be uploaded each time
            :type file: file
            :param file_type: The code of the file type (e.g., CBKS). Please see details of File Type Code.
            :type file_type: str
            :param poll_interval: Interval to poll the result from api, in seconds
            :type poll_interval: float
            :param timeout: Timeout in seconds
            :type timeout: float
        """
        start = time.time()
        task = client.extraction_async_create(file=open(file_path, "rb"),
                                              file_type=file_type)
        print(task.task_id)
        time.sleep(poll_interval)
        result = client.extraction_result(application_id=task.task_id)
        print(result)
        while result['data']['taskStatus'] in ['Doing', 'Init']:
            if time.time() - start > timeout:
                raise IDPException(f'Task timeout exceeded: {timeout}')
            time.sleep(poll_interval)
            result = client.extraction_result(application_id=task.task_id)
            print(result['data']['taskStatus'])
        if result['data']['taskStatus'] == 'Done':
            return result
        else:
            raise IDPException(f'Task timeout exceeded: {timeout}')


    result = run_simple_task(client, file_path="/your/file/path/upload/idp/test_file.pdf", file_type='CBKS')
    print(result)

3. Synchronous Information Extraction API
--------------------------------------------------------------------
3.1 Synchronous Submit File for Fields Extraction
--------------------------------------------------------------------
.. code-block:: python

    res = client.extraction_card_fields_sync(file=open("/your/file/path/upload/idp/test_file.pdf", "rb"), file_type='ZHID',lang='EN')
    print(res)


4. FAAS - Bank Statement Insight
--------------------------------------------------------------------
4.1 Create New Insight Case
~~~~~~~~~~~~
.. code-block:: python

    # Extract FAAS
    files = {
        "files": ("test.zip", open('/your/file/path/test.zip', 'rb'))
    }
    task = client.extraction_faas_create(files=files, customerType=1, countryId='100065', informationType=0)
    print(task.task_id)

4.2 To Get FAAS Insight Analysis Status By Insight Analysis Application Id
~~~~~~~~~~~~

.. code-block:: python

    application_id = '12345'
    status = client.extraction_faas_status(application_id=application_id)
    print(status)
4.3 Export FAAS Insight Analysis Result By Insight Analysis Application Id
~~~~~~~~~~~~
.. code-block:: python

    # this content could be a xlsx file or a zip file depending on your config on our system
    application_id = 'FAAS1234'
    client.refresh_token()
    content_bytes = client.extraction_faas_export(application_id=application_id)
    # NOTE: suffix could be zip or xlsx, take zip as a demo, it is decided by your company config on our system
    with open('/your/file/path/test.zip', 'wb') as f:
        f.write(content_bytes)


4.4 To Get FAAS Insight Analysis Result By Insight Analysis Application Id
~~~~~~~~~~~~
.. code-block:: python

    application_id = 'FAAS1234'
    res = client.extraction_faas_result(application_id=application_id)
    print(res)


4.5 Sample of create a simple faas extraction job and fetch result
~~~~~~~~~~~~
.. code-block:: python

    def run_simple_faas_task(client, files,
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
                         callbackMode: int = 0, poll_interval=60, timeout=12*60):
        # 1. create faas extraction task
        task = client.extraction_faas_create(files=files, customerType=customerType, countryId=countryId, regionId=regionId,
                                             informationType=informationType, cifNumber=cifNumber, borrowerName=borrowerName,
                                             loanAmount=loanAmount, applicationNumber=applicationNumber, applicationDate=applicationDate,
                                             currency=currency, rateDateType=rateDateType, rateFrom=rateFrom, rateDate=rateDate,
                                             automatic=automatic, hitlType=hitlType, industryType=industryType, industryBiCode=industryBiCode,
                                             ebitdaRatio=ebitdaRatio, relatedParties=relatedParties, supplierBuyer=supplierBuyer, checkAccountStr=checkAccountStr,
                                             callbackUrl=callbackUrl, autoCallback=autoCallback, callbackMode=callbackMode)
        print(task.task_id)
        time.sleep(poll_interval)
        start = time.time()

        # 2. get faas extraction task status
        status = client.extraction_faas_status(task.task_id)
        print(status)
        while status in ['Doing', 'Init']:
            if time.time() - start > timeout:
                raise IDPException(f'Task timeout exceeded: {timeout}')
            time.sleep(poll_interval)
            status = client.extraction_faas_status(task.task_id)
        if status == 'Done':
            result = client.extraction_faas_result(task.task_id)
            return result
        else:
            raise IDPException(f'Task timeout exceeded: {timeout} or {status} status code abnormal')


    files = {
        "files": ("test.zip", open('/your/file/path/test.zip', 'rb'))
    }
    result = run_simple_faas_task(client, files=files, customerType=1, countryId='100065', informationType=0)
    print(result)


5. Document Agent API
--------------------------------------------------------------------
5.1 Asynchronous Submit File For Document Agent
~~~~~~~~~~~~

.. code-block:: python

    task = client.extraction_doc_agent_create(flowCode='DAG1',file=open("your file path", "rb"))
    print(task.task_id)
    # this would be the application_id

5.2 Query Document Agent Application Status
~~~~~~~~~~~~

.. code-block:: python

    application_id = 'your application id'
    response = client.extraction_doc_agent_status(applicationId=application_id)
    print(status['data']['status'])

5.3 Export Result of Document Agent Application
~~~~~~~~~~~~

.. code-block:: python

    # NOTE: this could be a xlsx or a zip file depending on your config on our system
    application_id = 'your application id'
    content_bytes = client.extraction_doc_agent_export(applicationId=application_id)
    with open('/your/path/doc_agent/download/file.zip', 'wb') as f:
        f.write(content_bytes)
5.4 Sample of create a doc agent task and fetch the result
~~~~~~~~~~~~

.. code-block:: python

    import time
    from sixe_idp.api import Client, OauthClient, IDPException
    # This is only a demo showing a simple usage of doc agent api
    def run_simple_doc_agent_task(client, flowCode: int,
                        file_path,
                        poll_interval=30,
                        timeout=600,
                        result_file_dir = None,
                        callback: str = None,
                        autoCallback: bool = None,
                        callbackMode: int = None,
                        callbackQaCodes: str = None):
        # 1. create doc agent task
        task = client.extraction_doc_agent_create(flowCode=flowCode, file=open(file_path, "rb"))
        print(task.task_id)
        time.sleep(poll_interval)
        start = time.time()

        # 2. get doc agent task status
        response = client.extraction_doc_agent_status(applicationId=task.task_id)
        status = response['data']['status']
        print(status)
        while status in ['On Process']:
            if time.time() - start > timeout:
                raise IDPException(f'Task timeout exceeded: {timeout}')
            time.sleep(poll_interval)
            response = client.extraction_doc_agent_status(applicationId=task.task_id)
            status = response['data']['status']
            print(status)
        # 3. get doc agent result
        content_bytes = client.extraction_doc_agent_export(applicationId=task.task_id)
        with open(f'{result_file_dir}/{task.task_id}.xlsx', 'wb') as f:
            f.write(content_bytes)
        print(f"{task.task_id} end cost {time.time() - start} seconds")

    flowCode = "DAG1"
    file_path = "your file path"
    result_file_dir = "/your/result/path/dir"
    run_simple_doc_agent_task(client, flowCode=flowCode, file_path=file_path, result_file_dir=result_file_dir)


6. Split And Extraction
--------------------------------------------------------------------

6.1 Asynchronous Submit File for Split And Fields Extraction
~~~~~~~~~~~~

.. code-block:: python

    from sixe_idp.api import Client, OauthClient, IDPException
    split_and_extraction_task = client.split_and_extraction_async_create(file=open("/your/path/uploaded/Split And Extraction file.pdf", "rb"),group_id=3,lang='EN',hitl=False,extract_mode=3)
    print(split_and_extraction_task.task_id)

6.2 Get Status By ApplicationId for Split And Fields Extraction Task
~~~~~~~~~~~~

.. code-block:: python

    from sixe_idp.api import Client, OauthClient, IDPException
    application_id = 'your split and extraction application_id id' # like SE123456789
    split_and_extraction_task_status = client.split_and_extraction_status(application_id=application_id)
    print(split_and_extraction_task_status)

6.3 Get zip result By ApplicationId for Split And Fields Extraction Task
~~~~~~~~~~~~

.. code-block:: python

    from sixe_idp.api import Client, OauthClient, IDPException
    application_id = 'your split and extraction application_id id' # like SE123456789
    split_and_extraction_task_content_bytes = client.split_and_extraction_export(application_id=application_id)
    with open(f'/your/path/download/{application_id}.zip', 'wb') as f:
        f.write(split_and_extraction_task_content_bytes)