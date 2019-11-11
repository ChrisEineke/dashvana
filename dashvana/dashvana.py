from ruamel.yaml import YAML
import argparse
import json
import re
import StringIO

yaml = YAML(typ="safe")

class SimpleExpressionTranslator:
    def __init__(self):
        pass
    def translate(self, expression):
        if expression is None:
            return ExpressionTranslation(None, None)
        translated1 = re.sub(r"[({\[,\"! =\]})]", "_", expression)
        translated2 = re.sub(r"_+", "_", translated1)
        translated3 = re.sub(r"_*$", "", translated2)
        return ExpressionTranslation(expression, translated3)

class ExpressionTranslation:
    def __init__(self, expression, translation):
        self.expression = expression
        self.translation = translation

class PrometheusRecordingRules:
    def __init__(self, group_name):
        self.group_name = group_name
        self.rules = []
    def add_rule(self, expression_translation):
        self.rules.append({
            "record": expression_translation.translation,
            "expr": expression_translation.expression,
        })
    def find_translated_expression(self, expression):
        for rule in self.rules:
            if rule["expr"] is expression:
                return rule["record"]
        return None
    def write_yaml(self, stream):
        yaml.dump({
            "groups": {
                "name": self.group_name,
                "rules": self.rules,
            },
        }, stream)

class Dashvana:
    DEFAULT_GROUP_NAME = "default"
    def __init__(self, translator):
        self.translator = translator
    def process(self, dashboard_in_filepath, dashboard_out_filepath, group_name, rules_out_filepath):
        dashboard = None
        with open(dashboard_in_filepath) as dashboard_in_fp:
            dashboard = json.load(dashboard_in_fp)
        expressions = []
        for row in dashboard["rows"]:
            for panel in row["panels"]:
                for target in panel["targets"]:
                    expressions.append(target["expr"])
        translated_expressions = []
        for expression in expressions:
            translated_expressions.append(self.translator.translate(expression))
        prometheus_recording_rules = PrometheusRecordingRules(group_name)
        for translated_expression in translated_expressions:
            prometheus_recording_rules.add_rule(translated_expression)
        with open(dashboard_out_filepath, "w") as dashboard_out_fp:
            for row in dashboard["rows"]:
                for panel in row["panels"]:
                    for target in panel["targets"]:
                        target["expr"] = prometheus_recording_rules.find_translated_expression(target["expr"])
            json.dump(dashboard, dashboard_out_fp, indent=2)
        with open(rules_out_filepath, "w") as rules_out_fp:
            prometheus_recording_rules.write_yaml(rules_out_fp)
    @classmethod
    def main(cls):
        parser = argparse.ArgumentParser()
        parser.add_argument("--dashboard_in",  type=str, required=True, help="The path to the dashboard to translate.")
        parser.add_argument("--dashboard_out", type=str, required=True, help="The path to the translated dashboard.")
        parser.add_argument("--group_name",    type=str, default=Dashvana.DEFAULT_GROUP_NAME, help="The name of the recording rule group.")
        parser.add_argument("--rules_out",     type=str, required=True, help="The path to the recording rule file.")
        args = parser.parse_args()
        dashvana = Dashvana(SimpleExpressionTranslator())
        dashvana.process(args.dashboard_in, args.dashboard_out, args.group_name, args.rules_out)

if __name__== "__main__":
  Dashvana.main()
