import os
import logging
import json
import io
import time
from collections import OrderedDict

import jinja2

from homeassistant.util.yaml import loader
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

jinja = jinja2.Environment(loader=jinja2.FileSystemLoader("/"))

def load_yaml(fname, args={}):
    try:
        ll_gen = False
        with open(fname, encoding="utf-8") as f:
            if f.readline().lower().startswith("# lovelace_gen"):
                ll_gen = True

        if ll_gen:
            stream = io.StringIO(jinja.get_template(fname).render(args))
            stream.name = fname
            return loader.yaml.load(stream, Loader=loader.SafeLineLoader) or OrderedDict()
        else:
            with open(fname, encoding="utf-8") as config_file:
                return loader.yaml.load(config_file, Loader=loader.SafeLineLoader) or OrderedDict()
    except loader.yaml.YAMLError as exc:
        _LOGGER.error(str(exc))
        raise HomeAssistantError(exc)
    except UnicodeDecodeError as exc:
        _LOGGER.error("Unable to read file %s: %s", fname, exc)
        raise HomeAssistantError(exc)


def _include_yaml(ldr, node):
    args = {}
    if isinstance(node.value, str):
        fn = node.value
    else:
        fn, args, *_ = ldr.construct_sequence(node)
    fname = os.path.join(os.path.dirname(ldr.name), fn)
    try:
        return loader._add_reference(load_yaml(fname, args), ldr, node)
    except FileNotFoundError as exc:
        _LOGGER.error("Unable to include file %s: %s", fname, exc);
        raise HomeAssistantError(exc)

def _uncache_file(ldr, node):
    path = node.value
    timestamp = str(time.time())
    if '?' in path:
        return f"{path}&{timestamp}"
    return f"{path}?{timestamp}"

loader.load_yaml = load_yaml
loader.yaml.SafeLoader.add_constructor("!include", _include_yaml)
loader.yaml.SafeLoader.add_constructor("!file", _uncache_file)

async def async_setup(*_):
    return True
