serf-handler
====

naive integration layer for building service-discovery systems on top of [serf](http://serfdom.io).

also, it would handle `config_update` events/queries so you could extend it and integrate a distribution layer for your configuration service.

Note: the SerfHandler and SerfHandlerProxy are almost a copy of [serf-master](https://github.com/garethr/serf-master)

##Assumptions

There are some assumptions about the system that are already made:

- apps will handle communication failures, so it's ok to work with eventually consistent data (that's why you are using serf, is,t it?).
- apps could rely on dns to communicate, so the easiest way to support this pattern is by editing the `/etc/hosts` file.
- apps could rely on config files to discover other services, so the info must be parsed in several standards (for now, those are json and yaml).

##Usage

###Service discovery

- Checkout the repo.
- Configure your serf agents so they use the `tags` feature to expose the products and services they handle (and the port of each one). The role tag is a list of all different service types a node is serving.
- Create your rode catalogue by importing the `handler` module and extending the base handlers (`SerfHandler`, `ConsumerHandler` and `ConfigHandler`).
- Create the entry point with your node definition or just edit the `event_hanlder.py` script. This script must register all the roles and handlers.
- Set the entry point created on the previous step as your main serf event handler.
- Start serf.

Check the fixtures/serf_agent_config.json for an example of serf agent configuration. *Note that, due a limitation in serf, ports must be defined as strings.*

The files in the `conf` dir will be updated after every change in the cluster, so your apps could use them to discover products, services and nodes.

For a `/etc/hosts` based service discovery, you could just use a cron to move the `conf/fakedhosts.txt` file to `/etc/hosts`.

If you don't want to react to every event your agent receives, you could just create a cron to run the `members.py` every few seconds. This script asks serf for the membership table and, if it has changed, it updates the `conf/fakedhosts.txt`, `conf/services.yml` and `conf/services.json` files

###Configuration service

Send events or queries with a json payload. The payload has some restictions:

- size: the string size must be less than 512 bytes
- structure: the serialiazed object must have a concrete structure. Check the *config_update* event section

Event:

```
$ serf event config_updated '{"p":"product1","k":"security","v":12,"c":{"a":true,"b":["a","b"]}}'
```

Query:

```
# sending a query just to 'web' nodes
$ serf query -format=json -tag role=.*web.* config_updated '{"p":"product1","k":"security","v":12,"c":{"a":true,"b":["a","b"]}}'
# sending a query just to nodes related to the 'product1' product
$ serf query -format=json -tag products=.*product1.* config_updated '{"p":"product1","k":"security","v":12,"c":{"a":true,"b":["a","b"]}}'
```

Choosing between sending an event or a query could depend on the frequency your configuration changes and the scope of the change.

##The `config_update` protocol

In order to allow you to properly handle the configuration updates, the `config_update` payloads must have this structure:

```
{
	"p":"product1",
	"k":"security",
	"v":12,
	"c":{
		"user":"myUser",
		"pass":"mySecret"
	}
}
```

Where `p` is the name of the product, `k` is the key of the config been updated, `v` is the version of the change and `c` is the piece of configuration that has been updated.

After receiving the `config_update` message, the nodes interested in the piece of config changed, if their stored version is older than the received one, will update the related config file. Every piece of configuration is stored in a directory named like the product the config is about and in a json file. The name of that file will be the key of the piece of configuration. For example, the previous payload would be stored at `/path/to/your/configs/product1/security.json` as

```
{
    "_version": 12,
    "user": "myUser",
    "pass": "mySecret"
}
```
