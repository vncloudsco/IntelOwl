from django.db import migrations
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor,
    ForwardOneToOneDescriptor,
    ManyToManyDescriptor,
)

plugin = {'id': 1, 'python_module': {'health_check_schedule': None,
                                         'update_schedule': {'minute': '30', 'hour': '7', 'day_of_week': '*',
                                                             'day_of_month': '*', 'month_of_year': '*'},
                                         'module': 'threatfox.ThreatFox',
                                         'base_path': 'api_app.ingestors_manager.ingestors'},
              'schedule': {'minute': '30', 'hour': '7', 'day_of_week': '*', 'day_of_month': '*', 'month_of_year': '*'},
              'periodic_task': {'crontab': {'minute': '30', 'hour': '7', 'day_of_week': '*', 'day_of_month': '*',
                                            'month_of_year': '*'}, 'name': 'ThreatfoxIngestor',
                                'task': 'intel_owl.tasks.execute_ingestor', 'kwargs': '{"config_name": "ThreatFox"}',
                                'queue': 'default', 'enabled': False},
              'user': {'username': 'ThreatfoxIngestor', 'first_name': '', 'last_name': '', 'email': ''},
              'name': 'ThreatFox', 'description': 'Threatfox ingestor', 'disabled': True, 'soft_time_limit': 60,
              'routing_key': 'default', 'health_check_status': True, 'maximum_jobs': 10, 'delay': '00:00:00',
              'health_check_task': None, 'playbook_to_execute': 3, 'model': 'ingestors_manager.IngestorConfig'}
params = [{'python_module': {'module': 'threatfox.ThreatFox', 'base_path': 'api_app.ingestors_manager.ingestors'},
               'name': 'days', 'type': 'int', 'description': 'Days to check. From 1 to 7', 'is_secret': False,
               'required': True},
              {'python_module': {'module': 'threatfox.ThreatFox', 'base_path': 'api_app.ingestors_manager.ingestors'},
               'name': 'url', 'type': 'str', 'description': 'API endpoint', 'is_secret': False, 'required': True}]
values = [{'parameter': {
    'python_module': {'module': 'threatfox.ThreatFox', 'base_path': 'api_app.ingestors_manager.ingestors'},
    'name': 'days', 'type': 'int', 'description': 'Days to check. From 1 to 7', 'is_secret': False, 'required': True},
               'analyzer_config': None, 'connector_config': None, 'visualizer_config': None,
               'ingestor_config': 'ThreatFox', 'pivot_config': None, 'for_organization': False, 'value': 1,
               'updated_at': '2024-04-11T14:55:11.772272Z', 'owner': None}, {'parameter': {
    'python_module': {'module': 'threatfox.ThreatFox', 'base_path': 'api_app.ingestors_manager.ingestors'},
    'name': 'url', 'type': 'str', 'description': 'API endpoint', 'is_secret': False, 'required': True},
                                                                             'analyzer_config': None,
                                                                             'connector_config': None,
                                                                             'visualizer_config': None,
                                                                             'ingestor_config': 'ThreatFox',
                                                                             'pivot_config': None,
                                                                             'for_organization': False,
                                                                             'value': 'https://threatfox-api.abuse.ch/api/v1/',
                                                                             'updated_at': '2024-04-11T14:57:13.545029Z',
                                                                             'owner': None}]


def _get_real_obj(Model, field, value):
    def _get_obj(Model, other_model, value):
        if isinstance(value, dict):
            real_vals = {}
            for key, real_val in value.items():
                real_vals[key] = _get_real_obj(other_model, key, real_val)
            value = other_model.objects.get_or_create(**real_vals)[0]
        # it is just the primary key serialized
        else:
            if isinstance(value, int):
                if Model.__name__ == "PluginConfig":
                    value = other_model.objects.get(name=plugin["name"])
                else:
                    value = other_model.objects.get(pk=value)
            else:
                value = other_model.objects.get(name=value)
        return value

    if (
            type(getattr(Model, field))
            in [ForwardManyToOneDescriptor, ForwardOneToOneDescriptor]
            and value
    ):
        other_model = getattr(Model, field).get_queryset().model
        value = _get_obj(Model, other_model, value)
    elif type(getattr(Model, field)) in [ManyToManyDescriptor] and value:
        other_model = getattr(Model, field).rel.model
        value = [_get_obj(Model, other_model, val) for val in value]
    return value


def _create_object(Model, data):
    mtm, no_mtm = {}, {}
    for field, value in data.items():
        value = _get_real_obj(Model, field, value)
        if type(getattr(Model, field)) is ManyToManyDescriptor:
            mtm[field] = value
        else:
            no_mtm[field] = value
    try:
        o = Model.objects.get(**no_mtm)
    except Model.DoesNotExist:
        o = Model(**no_mtm)
        o.full_clean()
        o.save()
        for field, value in mtm.items():
            attribute = getattr(o, field)
            if value is not None:
                attribute.set(value)
        return False
    return True


def migrate(apps, schema_editor):
    Parameter = apps.get_model("api_app", "Parameter")
    PluginConfig = apps.get_model("api_app", "PluginConfig")
    PythonModule = apps.get_model("api_app", "PythonModule")
    python_path = plugin.pop("model")
    Model = apps.get_model(*python_path.split("."))

    pm = PythonModule.objects.get(
        module="threatfox.ThreatFox", base_path="api_app.ingestors_manager.ingestors"
    )
    if not Parameter.objects.filter(python_module=pm, name="url"):
        p = Parameter(
            name="url",
            type="str",
            description="API endpoint",
            is_secret=False,
            required=True,
            python_module=pm,
        )
        p.full_clean()
        p.save()

    if not Model.objects.filter(name=plugin["name"]).exists():
        exists = _create_object(Model, plugin)
        if not exists:
            for param in params:
                _create_object(Parameter, param)
            for value in values:
                _create_object(PluginConfig, value)


def reverse_migrate(apps, schema_editor):
    python_path = plugin.pop("model")
    Model = apps.get_model(*python_path.split("."))

    try:
        Model.objects.get(name=plugin["name"]).delete()
    except Model.DoesNotExist:
        pass  # nothing to reverse migrate

    Parameter = apps.get_model("api_app", "Parameter")
    PythonModule = apps.get_model("api_app", "PythonModule")

    pm = PythonModule.objects.get(
        module="threatfox.ThreatFox", base_path="api_app.ingestors_manager.ingestors"
    )
    Parameter.objects.filter(python_module=pm, name="url").delete()


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ('api_app', '0062_alter_parameter_python_module'),
        ('ingestors_manager', '0019_ingestor_config_malwarebazaar'),
    ]

    operations = [
        migrations.RunPython(
            migrate, reverse_migrate
        )
    ]

