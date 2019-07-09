from django.db import models

# Create your models here.

class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    creator = models.IntegerField()
    updator = models.IntegerField()

    class Meta:
        abstract = True


class WorkflowGroup(BaseModel):
    name = models.CharField(unique=True)
    desc = models.CharField()


class BluePrint(BaseModel):
    """Workflow definition
    """
    STATUS_CHOICES = (
        ("draft", "草稿"),
        ("enable", "激活"),
        ("disable", "禁用"),
        ("pause", "暂停"),
    )
    name = models.CharField()
    desc = models.CharField()
    schema_version = models.CharField('DSL 版本号')
    version = models.IntegerField()
    status = models.CharField(choices=STATUS_CHOICES)
    start_state = models.CharField()
    group = models.ForeignKey(WorkflowGroup)

    class Meta:
        verbo_name = '工作流定义'
        unique_together = (
            ('name', 'version'),
        )


class StateMeta(BaseModel):
    """状态是工作流引用执行任务的桥梁
    """

    name = models.CharField(unique=True)
    input_path = models.CharField()
    output_path = models.CharField()
    topic = models.CharField("任务队列监听的 topic")
    task = models.ForeignKey(TaskMeta, null=True, blank=True)
    is_end = models.BooleanField(default=False)
    desc = models.CharField()

    # TODO 改成 mysql 后使用 ArrayField
    next = models.CharField('下一个状态(们)')


class TaskGroup(BaseModel):
    name = models.CharField(unique=True)
    desc = models.CharField()


class TaskMeta(BaseModel):
    """Task definition
    """
    TYPE_CHOICES=(
        ('service', '服务调用'),
        ('choice', '决策'),
        ('succeed', '成功'),
        ('fail', '失败'),
        ('parallel', '并行'),
        ('join', '汇合'),
    )

    EXECUTE_TYPE_CHOICES = (
        ("sync", "同步"),
        ("async", "异步"),
    )

    name = models.CharField()
    version = models.IntegerField()
    type = models.CharField(choices=TYPE_CHOICES)
    execute_type = models.CharField('执行方式', choices=TYPE_CHOICES, default='sync')
    service_url = models.CharField('http url/grpc url')
    service_header = models.CharField('http header')
    service_method = models.CharField('http method')
    system_task = models.BooleanField('是否为系统默认任务', default=False)
    group = models.ForeignKey(TaskGroup)
    desc = models.CharField()

    class Meta:
        verbose_name = '任务定义'
        unique_together = (
            ('name', 'version'),
        )

    def execute(self, input):
        """执行工作流。其实不应该在 composer 中"""
        output = {}
        return output


class Workflow(BaseModel):
    STATUS_CHOICES = (
        ("scheduled", "已调度"),
        ("started", "已启动"),
        ("succeed", "成功"),
        ("failed", "失败"),
        ("pasued", "已暂停"),
    )
    uuid = models.CharField(unique=True)
    blueprint = models.ForeignKey(BluePrint)
    blueprint_name = models.CharField()
    blueprint_version = models.IntegerField()
    status = models.CharField(choices=STATUS_CHOICES)
    input = models.TextField('输入报文')

    class Meta:
        verbose_name = '工作流实例'


class State(BaseModel):
    """记录每个任务的状态
    这个表会非常大，根据业务规模，可考虑放到 elasticsearch 中"""
    STATUS_CHOICES = (
        ("scheduled", "已调度"),
        ("started", "已启动"),
        ("succeed", "成功"),
        ("failed", "失败"),
    )
    uuid = models.CharField(unique=True)
    workflow_id = models.CharField()
    meta_id = models.CharField()
    status = models.CharField(choices=STATUS_CHOICES)
    start_datetime = models.DateTimeField()
    finish_datetime = models.DateTimeField()
    next = models.CharField('下一个状态(们)')
    previous = models.CharField('上一个状态(们)')
    input = models.TextField('输入报文')

    # 下一个任务的输入报文是上一个任务的输出报文的子集
    output = models.TextField('输出报文')

    class Meta:
        verbose_name = '状态'