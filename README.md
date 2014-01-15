Simple Waiter
=============

A very basic scheduling system to split work accross different computers. Very useful if you are trying to run one task on a lot of EC2 machines for example.

Analogy used: We have a kitchen (MongoDB Database) that needs to deliver orders (record in the db). Waiters (./waiter.py process) go to the kitchen to pick up an order and deliver it (run a command with the arguments in the order).

## How to use

Let's start with a clean database.

    python waiter.py clean

And let's create an arbitrary number of jobs that need to be ran and load them in the database.

    ls /dev > orders.csv
    python waiter.py load orders.csv

Now let's look at the status of our jobs

    $ python waiter.py status
    [{u'count': 315, u'_id': u'READY'}]

Let's create a very simple task that needs to be executed to 'deliver' the order:

    $ cat > crunch.sh
    #!/bin/sh

    echo "Crunching on: $*"
    sleep 3
    echo "done!"

And start processing (You can start this command multiple time):

    $ python waiter.py deliver ./crunch.sh --some-param some-value
    Delivering {u'status': u'RUNNING', u'start': 1389825762.641031, u'_id': ObjectId('52d70e63bb335757841eb999'), u'arguments': [u'ttyw8']}
    Crunching on: --some-param some-value ttyw8
    done!
    .
    Delivering {u'status': u'RUNNING', u'start': 1389825765.650469, u'_id': ObjectId('52d70e63bb335757841eb99a'), u'arguments': [u'ttyw9']}
    Crunching on: --some-param some-value ttyw9
    done!
    .
    Ctrl-C

What is the status now?

    $ python waiter.py status
    [{u'count': 304, u'_id': u'READY'}, {u'count': 10, u'_id': u'DONE'}, {u'count': 1, u'_id': u'RUNNING'}]

We killed a job while it was running so it is never going to finish. You can reset RUNNING and ERROR jobs with the `reset` command.

    $ python waiter.py reset
    Reset orders

And you can get an extract of all jobs and their status like so.

    $ python waiter.py extract
    _id,status,waiter,start,stop,arguments,error
    52d70e63bb335757841eb9a4,READY,,,,[u'vn2'],
    52d70e63bb335757841eb9a5,READY,,,,[u'vn3'],
    52d70e63bb335757841eb86d,READY,,,,[u'afsc_type5'],
    52d70e63bb335757841eb9a1,DONE,Thomass-MacBook-Pro.local/88025,1389825786.714047,,[u'urandom'],

As you can see, each job saves the name of the waiter (hostname / pid by default) and a timestamp for starting and stopping.

That's all folks!

## Other important options

The example above assumes that you are running with a local mongodb database. If that is not the case, use the `--kitchen` option to let the waiter know where is the kitchen! (And if you need `--db` to change the database name.)


## License

MIT License

Copyright Pebble Technology / Thomas Sarlandie 2014

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
