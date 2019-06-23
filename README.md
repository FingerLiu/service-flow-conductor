# service flow conductor(SFC)

SFC 是微服务环境中的服务流程管理系统，主要用于微服务治理，解决微服务的混沌问题。
随着服务拆分力度越来越细，服务调用流程渐渐变成不可知论。
基于 opentracing 协议的各种链路追踪系统一定程度解决了出 bug 后排查定位难的问题，但是一种被动的过程。
与链路追踪系统不同， SFC 是服务调用的前序流程，在服务定义之处，即已确定。

SFC 并不是退步，而是微服务不断演进的产物。
与 SOA 不同，引入 SFC 后，每个微服务仍旧拥有独立的生命周期。并且由于服务调用流程统一交由 SFC 的流程引擎处理，
各微服务无需再关注上下游信息，进一步降低服务间的耦合。
某种层面上来说， SFC 是 ESB 的子集。

ESB(Enterprise service bus) 主要职能:

- 服务间消息路由
- 服务间消息监控和控制
- 解析上下文
- 控制服务的部署和版本
- 服务传输内容的序列化
- 事件处理，数据转换与映射，事件队列，安全，异常处理，协议转换，沟通规范约定和控制等。

SFC 主要职能:

- 服务间消息路由
- 调用流程控制与监控

# principle

- event
- pub/sub
- API 调用

# arch

- composer
- flow engine
- job executor
- message queue
- flow monitor
- scheduler

> TODO 图

## composer

通过图形化界面生成 workflow 的 blueprint。
blueprint 规定了工作流中的任务和如何决策。
blueprint 是符合 AWS state language DSL 的 json。

编辑/修改 blueprint
blueprint 版本控制

## flow engine

解析 blueprint 决策工作流执行流程的状态机。状态机各个组成部分参见**workflow**一章。

## job executor

调用或执行具体任务,理论上可以支持异步和同步两种模式，为了简单，暂时先只实现异步模式。

### async

异步模式下， job executor 主要负责消息的传递和转发。

input topic: raw_order_tmall
input consumer group: SFC

transfer topic: raw_order_tmall
transfer consumer group: order_split6

为了实现 job 上下游解耦，以及工作流控制， SFC 要对消息做一次转发(有性能损耗，待优化)。
SFC 中的每个服务无需关系自己是否有下游服务，以及有多少个下游服务。
假设服务 A 被两个业务流程共用，分别被 B， C 共用，pub/sub 模式和 conductor 模式消息传递如下。

data flow in pub/sub mode and conductor mode.

    pub/sub:
               A
               | topic: raw_order_tmall;consumer group: all
        _______|________
       |                |
       B                C

    conductor:
                    A
                    | topic: raw_order_tmall;consumer group: SFC 
                    |
                SFC(service flow conductor) 
                    |
         job-b______|_____________job-c
        |group: order_split        |group: finanical_statistic
        B                          C 

### sync
同步模式指的是 job 内部逻辑是同步的(RESTAPI, grpc)，job 与 job 之间的通信仍然是异步。
同步模式下，job exector 负责调用任务的 API，然后收集 API 返回结果，传递到下游的消息队列中。
同步模式有以下好处：

- 业务服务无需关心调用方法，不用实现 kafka 消息收发机制，只关心业务逻辑，降低编程复杂度
- 不需要 SFC 进行消息转发，没有额外性能损耗，同时降低对存储空间的占用。

缺点：
同步阻塞，降低了 SFC 的吞吐量。

## message queue

传递和存储任务的结果
目前仅支持 kafka
这个名字有点问题， 因为严格意义上说， kafka 的消息传递模式不是 queue, 而是 pub/sub。应该换个名字。

## flow monitor

查看每类 blueprint 统计信息
查看每个 flow 状态信息
启动/停止 blueprint
重试 flow

## scheduler
由于每个工作流的处理的数据流和处理效率差异很大，我们实现了一套调度器机制，为每个 workflow 动态地分配资源。
主要实现以下功能。

- 增加/删除 workflow
- 调整指定 workflow 的 job executor 副本数量
- 调整指定 state 的 job executor 副本数量(待确定)

更详细信息请查看 **behind the scenes**

# messaging

async 和 sync

## async

### kafka

topic 和 consumer group
例子：
topic: raw_order_tmall
consumer group: order_split1

# workflow 定义

## Version

## startstate

## states

example:

```json

"HelloWorld": {
  "Type": "Task",
  "Mode": "Sync",
  "Processor": "arn:aws:lambda:us-east-1:123456789012:function:HelloWorld",
  "Next": "NextState",
  "Comment": "Executes the HelloWorld Lambda function"
}
```

types

- Task
- Choice
- Parallel
- Succeed
- Fail
- Join(extend)

# DSL

Amazon States Language

https://states-language.net/spec.html

# E-R

# others

## netflix conductor

Conductor 是一个微服务编排引擎。

https://github.com/Netflix/conductor

http://dockone.io/article/1930

## aws step function

AWS Step Functions 将多个 AWS 服务协调为无服务器工作流。

https://aws.amazon.com/cn/step-functions/

## json path

## json schema

# behind the scenes
## 调度器
每建一个 workflow 生成一个新的资源。
这个资源是一个进程还是一个 docker contqiner?
调度器是使用 go plugin 还是 kubernetes?