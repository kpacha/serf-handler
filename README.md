serf-handler
====

naive integration layer for building service-discovery systems on top of [serf](http://serfdom.io).

also, it would handle `config_update` events/queries so you could extend it and integrate a distribution layer for your configuration service.

Note: the handler module is almost a copy of [serf-master](https://github.com/garethr/serf-master)