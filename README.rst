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
    # region has test and sea, sea for production env
    client_id = 'your client id found on web'
    client_secret = 'your client secret found on web'
    oauth = OauthClient(region='test').get_IDP_new_authorization(clientId=client_id, clientSecret=client_secret)
    client = Client(region='test', token=oauth, isOauth=True)
    

2. Asynchronous Information Extraction API
--------------------------------------------------------------------

2.1 Asynchronous Submit File for Fields Extraction
~~~~~~~~~~~~
.. code-block:: python

    # We have multiple ways to create the IDP task, and we only show CBKS file type as a demo
    task = client.extraction_async_create(file=open("your file path", "rb"),file_type='CBKS')
    print(task.task_id)


2.2 To Get Fields Extraction Result By TaskId
~~~~~~~~~~~~
.. code-block:: python

    task_id = '12345'
    task_result = client.extraction_result(task_id=task_id) # try to fetch the result
    print(task_result)


2.3 Query History Task List
~~~~~~~~~~~~
.. code-block:: python

    history = client.extraction_task_history(page=1,limit=10)


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
        result = client.extraction_result(task_id=task.task_id)
        print(result)
        while result['data']['taskStatus'] in ['Doing','Init']:
            if time.time() - start > timeout:
                raise IDPException(f'Task timeout exceeded: {timeout}')
            time.sleep(poll_interval)
            result = client.extraction_result(task_id=task.task_id)
            print(result['data']['taskStatus'])
        if result['data']['taskStatus'] == 'Done':
            return result
        else:
            raise IDPException(f'Task timeout exceeded: {timeout}')

    oauth = OauthClient(region='sea').get_IDP_new_authorization(clientId='your client id', clientSecret='your client secret')
    client = Client(region='sea', token=oauth, isOauth=True)
    result = run_simple_task(client, file_path="your file path", file_type='CBKS')
    print(result)

3. FAAS - Bank Statement Insight
--------------------------------------------------------------------
3.1 Create New Insight Case
~~~~~~~~~~~~
.. code-block:: python

    # Extract FAAS
    files = {
        "files": ("test.zip", open('/your/file/path/test.zip', 'rb'))
    }
    task = client.extraction_faas_create(files=files, customerType=1, countryId='100065', informationType=0)
    print(task.task_id)


3.2 Export FAAS Insight Analysis Result By Insight Analysis Application Id
~~~~~~~~~~~~
.. code-block:: python

    # this content could be a xlsx file or a zip file depending on your config on our system
    task_id = 'FAAS1234'
    content_bytes = client.extraction_faas_export(task_id=task_id)
    # suffix could be zip or xlsx, take zip as a demo
    with open('/your/file/path/test.zip', 'wb') as f:
        f.write(content_bytes)


3.3 To Get FAAS Insight Analysis Result By Insight Analysis Application Id
~~~~~~~~~~~~
.. code-block:: python

    task_id = 'FAAS1234'
    res = client.extraction_faas_result(task_id=task_id)
    print(res)


4. Document Agent API
--------------------------------------------------------------------
4.1 Asynchronous Submit File For Document Agent
~~~~~~~~~~~~

.. code-block:: python

    task = client.extraction_doc_agent_create(flowCode='DAG1',file=open("your file path", "rb"))
    print(task.task_id)
    # this would be the application_id

4.2 Query Document Agent Application Status
~~~~~~~~~~~~

.. code-block:: python

    application_id = 'your application id'
    status = client.extraction_doc_agent_status(applicationId=application_id)
    print(status)

4.3 Export Result of Document Agent Application
~~~~~~~~~~~~

.. code-block:: python

    # this could be a xlsx or a zip file depending on your config on our system
    application_id = 'your application id'
    content_bytes = client.extraction_doc_agent_export(applicationId=application_id)
    with open('/your/path/result/file.xlsx', 'wb') as f:
        f.write(content_bytes)
4.4 Sample of create a doc agent task and fetch the result
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
        task = client.extraction_doc_agent_create(flowCode=flowCode, file=open(file_path, "rb"))
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

    oauth = OauthClient(region='sea').get_IDP_new_authorization(clientId='your client id', clientSecret='your client secret')
    client = Client(region='sea', token=oauth, isOauth=True)
    flowCode = "DAG1"
    file_path = "your file path"
    result_file_dir = "/your/result/path/dir"
    run_simple_doc_agent_task(client, flowCode=flowCode, file_path=file_path, result_file_dir=result_file_dir)
