Usages
=================

Setup
-----------------

.. code-block:: bash

    $ pip install 6estates-idp      


Run extraction task (the simple way)
---------------------------------------------------
.. code-block:: python

    from sixe_idp.api import Client, FileType
    client = Client(region='sea', token='your-token-here')
    task_result = client.extraction_task.run_simple_task(file=open("[UOB]202103_UOB_2222.pdf","rb"), file_type=FileType.bank_statement)


Run extraction task (the harder way)
---------------------------------------------------

.. code-block:: python

    from sixe_idp.api import Client, Task, TaskResult, IDPException, FileType  

    client: Client = Client(region='test', token='your-token-here')

    task: Task = client.extraction_task.create(file=open('path-to-the-file'), file_type=FileType.bank_statement)

    task_result: TaskResult = client.extraction_task.result(task_id=task.task_id)

    while task_result.status == 'Doing' or task_result.status=='Init':

        time.sleep(3)

        task_result = client.extraction_task.result(task_id=task.task_id)

    print(task_result.fields)
