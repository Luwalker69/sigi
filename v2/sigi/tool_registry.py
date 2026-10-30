"""Catalogue de capacités : les mêmes outils sont décrits et exécutables."""

import copy


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, specification, handler):
        name = specification["function"]["name"]
        if name in self._tools:
            raise ValueError("Outil déjà enregistré.")
        self._tools[name] = (copy.deepcopy(specification), handler)

    @property
    def tool_specs(self):
        return [copy.deepcopy(specification) for specification, _ in self._tools.values()]

    def invoke(self, name, arguments):
        if name not in self._tools or not isinstance(arguments, dict):
            raise ValueError("Outil ou arguments inconnus.")
        specification, handler = self._tools[name]
        schema = specification["function"]["parameters"]
        properties = schema["properties"]
        if set(arguments) - set(properties) or set(schema.get("required", [])) - set(arguments):
            raise ValueError("Arguments inattendus ou manquants.")
        types = {"string": str, "integer": int, "boolean": bool}
        for key, value in arguments.items():
            expected = types.get(properties[key].get("type"))
            if expected and type(value) is not expected:
                raise ValueError("Type d'argument invalide.")
        return handler(**arguments)
