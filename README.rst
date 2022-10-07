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

    $ pip install 6estates-idp      


Usage 
============ 
1. Initialize the 6Estates IDP Client 
---------------------------------------------------------------------

6E API Access Token(Deprecated)

.. code-block:: python

    from sixe_idp.api import Client, FileType
    
    client = Client(region='sea', token='your-token-here')


6E API Authorization based on oauth 2.0

.. code-block:: python

    from sixe_idp.api import Client, OauthClient, FileType
    
    oauth = OauthClient(region='sea').get_IDP_authorization(authorization ='your-authorization-here')
    client = Client(region='sea', token=oauth, isOauth=True)
    
    
2. To Extract Fields in Synchronous Way 
---------------------------------------------------------------------

If you just need to do one file at a time

.. code-block:: python

    from sixe_idp.api import Client, FileType
    
    client = Client(region='sea', token='your-token-here')
    task_result = client.extraction_task.run_simple_task(file=open("[UOB]202103_UOB_2222.pdf","rb"), file_type=FileType.bank_statement)


3. To Extract Fields in Asynchronous Way
--------------------------------------------------------------------

If you need to do a batch of files

.. code-block:: python

    from sixe_idp.api import Client, Task, TaskResult, IDPException, FileType  

    client: Client = Client(region='test', token='your-token-here')

    task: Task = client.extraction_task.create(file=open("path-to-the-file"), file_type=FileType.bank_statement)

    task_result: TaskResult = client.extraction_task.result(task_id=task.task_id)

    while task_result.status == 'Doing' or task_result.status=='Init':

        time.sleep(3)

        task_result = client.extraction_task.result(task_id=task.task_id)

    print(task_result.raw)
