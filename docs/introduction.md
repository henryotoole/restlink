# Introduction

RESTLink is a python module that automates the exposure of backend resources like databases via a REST API.

Any toolchain that aims to expose a secured backend resource like a database table to the open internet
must tackle a great deal of possible complexity. There are *a lot of ways to do this* and plenty of other
excellent projects automate one part or another of the toolchain. RESTLink automates the whole toolchain,
but only along a very specific path or two.

Given a backend framework (like Flask) and a backend resource (like a relational database table), RESTLink
will expose and document a series of routes that enable the resource to be reached via classical REST API.
In simple (and for me, most) cases, the programmer must expend only limited effort to achieve this.
This includes:
+ The creation of a Marshmallow Schema for the resource,
+ Definition of an authentication method for requests,
+ Exposure of a method for backend resource general access (e.g. a fetcher for a SQLAlchemy `Session` instance)

Currently the only supported backend framework is Flask and the only supported backend resource is a relational 
database table via SQLAlchemy. Support for other frameworks and resources is planned.