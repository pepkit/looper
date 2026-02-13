"""Tests for pipestat config handoff validation."""

import pytest

from looper.exceptions import PipelineInterfaceConfigError
from looper.pipeline_interface import PipelineInterface


class TestPipestatHandoffValidation:
    """Tests for pipestat config handoff validation in PipelineInterface."""

    def test_cli_handoff_with_config_file(self, tmp_path):
        """Interface with {pipestat.config_file} in command_template passes validation."""
        piface_content = """
pipeline_name: test_pipeline
pipeline_type: sample
output_schema: schema.yaml
command_template: >
    python pipeline.py --pipestat-config {pipestat.config_file}
"""
        piface_path = tmp_path / "piface.yaml"
        piface_path.write_text(piface_content)

        # Should not raise
        pi = PipelineInterface(str(piface_path))
        assert pi.pipeline_name == "test_pipeline"

    def test_cli_handoff_with_other_pipestat_var(self, tmp_path):
        """Interface with any {pipestat.*} in command_template passes validation."""
        piface_content = """
pipeline_name: test_pipeline
pipeline_type: sample
output_schema: schema.yaml
command_template: >
    python pipeline.py {pipestat.results_file} {pipestat.output_schema}
"""
        piface_path = tmp_path / "piface.yaml"
        piface_path.write_text(piface_content)

        # Should not raise
        pi = PipelineInterface(str(piface_path))
        assert pi.pipeline_name == "test_pipeline"

    def test_cli_handoff_in_sample_interface(self, tmp_path):
        """Interface with {pipestat.*} in sample_interface.command_template passes."""
        piface_content = """
pipeline_name: test_pipeline
output_schema: schema.yaml
sample_interface:
    pipeline_type: sample
    command_template: >
        python pipeline.py --config {pipestat.config_file}
"""
        piface_path = tmp_path / "piface.yaml"
        piface_path.write_text(piface_content)

        # Should not raise
        pi = PipelineInterface(str(piface_path))
        assert pi.pipeline_name == "test_pipeline"

    def test_cli_handoff_in_project_interface(self, tmp_path):
        """Interface with {pipestat.*} in project_interface.command_template passes."""
        piface_content = """
pipeline_name: test_pipeline
output_schema: schema.yaml
project_interface:
    pipeline_type: project
    command_template: >
        python pipeline.py --config {pipestat.config_file}
"""
        piface_path = tmp_path / "piface.yaml"
        piface_path.write_text(piface_content)

        # Should not raise
        pi = PipelineInterface(str(piface_path))
        assert pi.pipeline_name == "test_pipeline"

    def test_env_var_handoff(self, tmp_path):
        """Interface with PIPESTAT_CONFIG in inject_env_vars passes validation."""
        piface_content = """
pipeline_name: test_pipeline
pipeline_type: sample
output_schema: schema.yaml
inject_env_vars:
    PIPESTAT_CONFIG: "{pipestat.config_file}"
command_template: >
    python pipeline.py
"""
        piface_path = tmp_path / "piface.yaml"
        piface_path.write_text(piface_content)

        # Should not raise
        pi = PipelineInterface(str(piface_path))
        assert pi.pipeline_name == "test_pipeline"

    def test_missing_handoff_raises_error(self, tmp_path):
        """Interface with output_schema but no handoff mechanism raises error."""
        piface_content = """
pipeline_name: test_pipeline
pipeline_type: sample
output_schema: schema.yaml
command_template: >
    python pipeline.py --no-pipestat-handoff
"""
        piface_path = tmp_path / "piface.yaml"
        piface_path.write_text(piface_content)

        with pytest.raises(PipelineInterfaceConfigError) as exc_info:
            PipelineInterface(str(piface_path))

        error_msg = str(exc_info.value)
        assert "test_pipeline" in error_msg
        assert "output_schema" in error_msg
        assert "pipestat" in error_msg.lower()

    def test_no_output_schema_skips_validation(self, tmp_path):
        """Interface without output_schema skips pipestat validation entirely."""
        piface_content = """
pipeline_name: test_pipeline
pipeline_type: sample
command_template: >
    python pipeline.py --regular-pipeline
"""
        piface_path = tmp_path / "piface.yaml"
        piface_path.write_text(piface_content)

        # Should not raise - no pipestat, no validation
        pi = PipelineInterface(str(piface_path))
        assert pi.pipeline_name == "test_pipeline"

    def test_pipestat_config_required_false_skips_validation(self, tmp_path):
        """Setting pipestat_config_required: false disables validation."""
        piface_content = """
pipeline_name: test_pipeline
pipeline_type: sample
output_schema: schema.yaml
pipestat_config_required: false
command_template: >
    python pipeline.py --custom-pipestat-handling
"""
        piface_path = tmp_path / "piface.yaml"
        piface_path.write_text(piface_content)

        # Should not raise due to pipestat_config_required: false
        pi = PipelineInterface(str(piface_path))
        assert pi.pipeline_name == "test_pipeline"

    def test_error_message_includes_guidance(self, tmp_path):
        """Error message includes clear guidance on how to fix the issue."""
        piface_content = """
pipeline_name: my_pipeline
pipeline_type: sample
output_schema: schema.yaml
command_template: >
    python pipeline.py
"""
        piface_path = tmp_path / "piface.yaml"
        piface_path.write_text(piface_content)

        with pytest.raises(PipelineInterfaceConfigError) as exc_info:
            PipelineInterface(str(piface_path))

        error_msg = str(exc_info.value)
        # Should mention both options
        assert "command_template" in error_msg
        assert "inject_env_vars" in error_msg
        assert "PIPESTAT_CONFIG" in error_msg
        # Should mention override option
        assert "pipestat_config_required: false" in error_msg


class TestInjectEnvVars:
    """Tests for inject_env_vars rendering in submission scripts."""

    def test_inject_env_vars_renders_templates(self, tmp_path):
        """inject_env_vars templates are rendered with namespaces."""
        from looper.utils import render_inject_env_vars

        inject_env_vars = {
            "PIPESTAT_CONFIG": "{pipestat.config_file}",
            "OUTPUT_DIR": "{looper.output_dir}",
        }
        namespaces = {
            "pipestat": {"config_file": "/path/to/pipestat_config.yaml"},
            "looper": {"output_dir": "/path/to/output"},
        }

        result = render_inject_env_vars(inject_env_vars, namespaces)

        assert result["PIPESTAT_CONFIG"] == "/path/to/pipestat_config.yaml"
        assert result["OUTPUT_DIR"] == "/path/to/output"

    def test_inject_env_vars_schema_valid(self, tmp_path):
        """inject_env_vars passes schema validation."""
        piface_content = """
pipeline_name: test_pipeline
pipeline_type: sample
output_schema: schema.yaml
inject_env_vars:
    PIPESTAT_CONFIG: "{pipestat.config_file}"
    CUSTOM_VAR: "static_value"
    DYNAMIC_VAR: "{looper.output_dir}/subdir"
command_template: >
    python pipeline.py
"""
        piface_path = tmp_path / "piface.yaml"
        piface_path.write_text(piface_content)

        # Should pass schema validation
        pi = PipelineInterface(str(piface_path))
        assert pi.get("inject_env_vars") is not None
        assert pi["inject_env_vars"]["PIPESTAT_CONFIG"] == "{pipestat.config_file}"
        assert pi["inject_env_vars"]["CUSTOM_VAR"] == "static_value"
