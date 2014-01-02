# prodstate

### Description

Prodstate is a project for managing a tree of Redis instances for
quickly and reliably propagating state information across a large
production cluster (10,000+ machines).

In essence, prodstate is designed for data that fits a certain pattern:

* Available from every machine
* Quick updates (sub-second normal case, worst case several seconds)
* Needs to be correct (no missing updates)
* Relatively small in size (tens of megabytes)
* Data change rate is relatively small
* Many more reads than writes

In my own experience, this is useful for things like: which databases
are presently active, service discovery, certain machine level
organizational data, etc.

This is NOT a system that is designed to store data that is of interest
only to a small subset of your machine population. Since prodstate
distributes the data to every machine, the dataset should be useful to
nearly every machine. Global state information.

### Installation

Available in PyPi:

```bash
pip install prodstate
```

You will also need to have installed [Redis](http://redis.io). I
recommend the 2.8 series.

### Setup and Configuration

(to be written)

### Failure Handling

This is a distributed system, and there are several main types of
failures that can happen. (There are many more failures that can happen,
too, but I am only calling out the main ones.)

__Network partition.__

The immediate effect is that anybody who is on the side of the partition
without the root node will stop getting updates.

At the moment, prodstate does not correct for partitions. Nodes
will know when they stop receiving data, and the branches that lose
connection to the root will retry, but no action is presently taken to
address the situation.

__Root crash/failure.__

If a root fails in such a way as to become unreachable, presently the
cluster stops permitting writes (since only root nodes are writeable).
Prodstate does not yet self-recover from a root failure, so an
administrator will need to designate a new root.

A goal is to allow us to determine that the root has failed, and
to promote one of the branches to be the new root. Since they are
interchangeable in our model, this is safe.

__Branch failure.__

If a branch becomes unreachable, all leaf nodes that were using it will
find a new branch to move to. This failure is handled automatically
without operator intervention.

(more to come)

### Monitoring

This section contains some guidelines for monitoring your prodstate
cluster.

The main monitoring is that you should, on every machine in which you
run prodstate, monitor the local Redis instance for:

* Availability (make sure it's up)

* Latency (measure the 'time' key and see if it stops advancing, or if
  it's too far behind)

As long as the Redis instance is available and 'time' is advancing, then
prodstate data is available on this machine.

Separately, you will also want to monitor the prodstate Python program
itself to make sure that it's up and running.

### Limitations

Prodstate has been tested up to about 100MB of data, at which point the
author felt it was getting unwieldy and global resyncs were becoming
difficult.

Due to the nature of Redis replication, every time a slave switches
masters, it replicates the entirety of the dataset. There is no smart
replication to pick up where it left off, since Redis doesn't know that
the new master has the same dataset.

Because of this, certain actions will cause every Redis instance
globally to need to resync. Root failures/changes notably, but even a
branch failure will cause all of the leafs to have to resync. If you
have 10,000 servers, a 100MB dataset being resynced globally will be
nearly a terabyte of data to move around.

### On Redis

The basic premise of prodstate is that it is a program for managing the
configuration and replication of a cluster of Redis instances.

Redis itself is basically a "data structure server". It provides
you with the ability to connect to it and manage scalars, lists,
sets, hashes, and several other structures. It also provides pub/sub
mechanisms.

This makes Redis ideal for a global state store. In my experience, most
state is of the form "give me the DSN for the active foobar database",
that fits well in a hash structure. Similarly, "give me machines that
are running monkey instances" is a set.

Redis also has robust replication built-in, so master/slave is easy to
set up and works well. Prodstate extends this concept into, perhaps, a
way that the Redis authors didn't intend: a giant tree of thousands of
instances replicating the same set of data.

### Todo

* Implement a Nagios plugin that can run on each machine and monitor
  prodstate correctly.

### Known Bugs

Almost certainly quite many. This is a very young project.
