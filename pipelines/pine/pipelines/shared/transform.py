#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# **********************************************************************
# Copyright (C) 2018 Johns Hopkins University Applied Physics Laboratory
#
# All Rights Reserved.
# This material may only be used, modified, or reproduced by or for the
# U.S. government pursuant to the license rights granted under FAR
# clause 52.227-14 or DFARS clauses 252.227-7013/7014.
# For any other permission, please contact the Legal Office at JHU/APL.
# **********************************************************************
import inspect


def transform_module_by_config(module_ref, config_ref, config_prefix=None):
    """
    Transforms a given module's properties based on ConfigBuilder Values.
    The prefix can be used to avoid blindy changing values and target a subset of matching values in config_ref.
    :type module_ref: ModuleType
    :type config_ref: dict
    :type config_prefix: str
    """
    if not inspect.ismodule(module_ref):
        return
    config_prefix = config_prefix if isinstance(config_prefix, str) else ""
    valid_types = frozenset({str, int, float, bytes, bool, tuple, list, dict})
    member_list = inspect.getmembers(module_ref, lambda x: not (inspect.isroutine(x) or inspect.ismodule(x) or inspect.isclass(x)))
    attribute_list = [mem for mem in member_list if not (mem[0].startswith("__") and mem[0].endswith("__"))]
    filtered_list = [mem for mem in attribute_list if type(mem[1]) in valid_types]
    for key in dict(filtered_list):
        key_to_get = config_prefix + key.upper()
        has_key = key_to_get in config_ref
        if not has_key:
            continue
        key_val = getattr(config_ref, key_to_get, None) or dict.get(config_ref, key_to_get, None)
        if type(key_val) in valid_types:
            setattr(module_ref, key, key_val)
