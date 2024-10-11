6Estates idp-python
==============
A Python SDK for communicating with the 6Estates Intelligent Document Processing(IDP) Platform.


Documentation
-----------------

The documentation for the 6Estates IDP API can be found via https://idp-sea.6estates.com/docs

The Python library documentation can be found via https://idp-sdk-doc.6estates.com/python/.


Setup
-----------------

.. code-block:: bash

    pip install 6estates-idp


Usage 
============ 
1. Initialize the 6Estates IDP Client 
---------------------------------------------------------------------

6E API Authorization based on oauth(Deprecated)

.. code-block:: python

    import time
    from sixe_idp.api import Client, OauthClient
    # region has test and sea, sea for production env
    http_header = 'Basic x...' # your http header, normal begin with Basic
    oauth = OauthClient(region='test').get_IDP_authorization(http_header)
    oauth_client = Client(region='test', token=oauth, isOauth=True)


6E API Authorization based on oauth 2.0(Recommended)

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

