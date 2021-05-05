""" Tests for use of sample subtypes in PipelineInterface. """

import inspect
import itertools
import os
import sys

if sys.version_info < (3,):
    import __builtin__ as builtins
else:
    import builtins

import mock
import pytest

from looper import Sample
from looper.pipeline_interface import SUBTYPE_MAPPING_SECTION as SUBTYPES_KEY
from looper.pipeline_interface import PipelineInterface

from .conftest import ATAC_PROTOCOL_NAME, write_config_data

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


SAMPLE_IMPORT = "from looper import Sample"


class CustomExceptionA(Exception):
    def __init__(self, *args):
        super(CustomExceptionA, self).__init__(*args)


class CustomExceptionB(Exception):
    def __init__(self, *args):
        super(CustomExceptionB, self).__init__(*args)


CUSTOM_EXCEPTIONS = [CustomExceptionA, CustomExceptionB]

# Test case parameterization, but here for import locality and
# to reduce clutter in the pararmeterization declaration.
_, BUILTIN_EXCEPTIONS_WITHOUT_REQUIRED_ARGUMENTS = list(
    map(
        list,
        zip(
            *inspect.getmembers(
                builtins,
                lambda o: inspect.isclass(o)
                and issubclass(o, BaseException)
                and not issubclass(o, UnicodeError),
            )
        ),
    )
)


class SampleSubtypeTests:
    """PipelineInterface attempts import of pipeline-specific Sample."""

    # Basic cases
    # 1 -- unmapped pipeline
    # 2 -- subtypes section is single string
    # 3 -- subtypes section is mapping ()
    # 4 -- subtypes section is missing (use single Sample subclass if there is one, base Sample for 0 or > 1 Sample subtypes defined)
    # 5 -- subtypes section is null  --> ALWAYS USE BASE SAMPLE (backdoor user side mechanism for making this be so)

    # Import trouble cases
    # No __main__
    # Argument parsing
    # missing import(s)

    # Subcases
    # 2 -- single string
    # 2a -- named class isn't defined in the module
    # 2b -- named class is in module but isn't defined
    #

    PROTOCOL_NAME_VARIANTS = [
        "ATAC-Seq",
        "ATACSeq",
        "ATACseq",
        "ATAC-seq",
        "ATAC",
        "ATACSEQ",
        "ATAC-SEQ",
        "atac",
        "atacseq",
        "atac-seq",
    ]

    @pytest.mark.parametrize(
        argnames="pipe_key",
        argvalues=["{}.py".format(proto) for proto in PROTOCOL_NAME_VARIANTS],
    )
    @pytest.mark.parametrize(argnames="protocol", argvalues=PROTOCOL_NAME_VARIANTS)
    def test_pipeline_key_match_is_strict(
        self, tmpdir, pipe_key, protocol, atac_pipe_name, atacseq_iface_with_resources
    ):
        """Request for Sample subtype for unmapped pipeline is KeyError."""

        # Create the PipelineInterface.
        strict_pipe_key = atac_pipe_name
        protocol_mapping = {protocol: strict_pipe_key}
        confpath = write_config_data(
            protomap=protocol_mapping,
            dirpath=tmpdir.strpath,
            conf_data={strict_pipe_key: atacseq_iface_with_resources},
        )
        piface = PipelineInterface(confpath)

        # The absolute pipeline path is the pipeline name, joined to the
        # PipelineInterface's pipelines location. This location is the
        # location from which a Sample subtype import is attempted.
        full_pipe_path = os.path.join(tmpdir.strpath, atac_pipe_name)

        # TODO: update to pytest.raises(None) if/when 3.1 adoption.
        # Match between pipeline key specified and the strict key used in
        # the mapping --> no error while mismatch --> error.
        if pipe_key == atac_pipe_name:
            piface.fetch_sample_subtype(
                protocol, pipe_key, full_pipe_path=full_pipe_path
            )
        else:
            with pytest.raises(KeyError):
                piface.fetch_sample_subtype(
                    protocol, pipe_key, full_pipe_path=full_pipe_path
                )

    @pytest.mark.parametrize(
        argnames=["mapped_protocol", "requested_protocol"],
        argvalues=itertools.combinations(PROTOCOL_NAME_VARIANTS, 2),
    )
    def test_protocol_match_is_fuzzy(
        self,
        tmpdir,
        mapped_protocol,
        atac_pipe_name,
        requested_protocol,
        atacseq_piface_data,
    ):
        """Punctuation and case mismatches are tolerated in protocol name."""

        # Needed to create the PipelineInterface.
        protomap = {mapped_protocol: atac_pipe_name}
        # Needed to invoke the function under test.
        full_pipe_path = os.path.join(tmpdir.strpath, atac_pipe_name)

        # PipelineInterface data provided maps name to actual interface data
        # Mapping, so modify the ATAC-Seq mapping within that.
        # In this test, we're interested in the resolution of the protocol
        # name, that with it we can grab the name of a class. Thus, we
        # need only an arbitrary class name about which we can make the
        # relevant assertion(s).
        test_class_name = "TotallyArbitrary"
        atacseq_piface_data[atac_pipe_name][SUBTYPES_KEY] = test_class_name

        # Write out configuration data and create the PipelineInterface.
        conf_path = write_config_data(
            protomap=protomap, conf_data=atacseq_piface_data, dirpath=tmpdir.strpath
        )
        piface = PipelineInterface(conf_path)

        # Make the call under test, patching the function protected
        # function that's called iff the protocol name match succeeds.
        with mock.patch(
            "looper.pipeline_interface._import_sample_subtype", return_value=None
        ) as mocked_import:
            # Return value is irrelevant; the effect of the protocol name
            # match/resolution is entirely observable via the argument to the
            # protected import function.
            piface.fetch_sample_subtype(
                protocol=requested_protocol,
                strict_pipe_key=atac_pipe_name,
                full_pipe_path=full_pipe_path,
            )
        # When the protocol name match/resolution succeeds, the name of the
        # Sample subtype class to which it was mapped is passed as an
        # argument to the protected import function.
        mocked_import.assert_called_with(full_pipe_path, test_class_name)

    @pytest.mark.parametrize(
        argnames="error_type",
        argvalues=[
            e
            for e in CUSTOM_EXCEPTIONS + BUILTIN_EXCEPTIONS_WITHOUT_REQUIRED_ARGUMENTS
            if e != StopIteration
        ],
    )
    def test_problematic_import_builtin_exception(
        self, tmpdir, error_type, atac_pipe_name, atacseq_piface_data
    ):
        """Base Sample is used if builtin exception on pipeline import."""

        # Values needed for object creation and function invocation
        protocol = ATAC_PROTOCOL_NAME
        protocol_mapping = {protocol: atac_pipe_name}
        full_pipe_path = os.path.join(tmpdir.strpath, atac_pipe_name)

        # Modify the data for the PipelineInterface and create it.
        atacseq_piface_data[atac_pipe_name][SUBTYPES_KEY] = {
            protocol: "IrrelevantClassname"
        }
        conf_path = write_config_data(
            protomap=protocol_mapping,
            conf_data=atacseq_piface_data,
            dirpath=tmpdir.strpath,
        )
        piface = PipelineInterface(conf_path)

        # We want to test the effect of an encounter with an exception during
        # the import attempt, so patch the relevant function with a function
        # to raise the parameterized exception type.
        with mock.patch("peppy.utils.import_from_source", side_effect=error_type()):
            subtype = piface.fetch_sample_subtype(
                protocol=protocol,
                strict_pipe_key=atac_pipe_name,
                full_pipe_path=full_pipe_path,
            )
        # When the import hits an exception, the base Sample type is used.
        assert subtype is Sample

    @pytest.mark.parametrize(
        argnames="num_sample_subclasses",
        argvalues=[0, 1, 2],
        ids=lambda n_samples: " num_sample_subclasses = {} ".format(n_samples),
    )
    @pytest.mark.parametrize(
        argnames="decoy_class",
        argvalues=[False, True],
        ids=lambda decoy: " decoy_class = {} ".format(decoy),
    )
    def test_no_subtypes_section(
        self,
        tmpdir,
        path_config_file,
        atac_pipe_name,
        num_sample_subclasses,
        decoy_class,
    ):
        """DEPENDS ON PIPELINE MODULE CONTENT"""

        # Basic values to invoke the function under test
        pipe_path = os.path.join(tmpdir.strpath, atac_pipe_name)
        piface = PipelineInterface(path_config_file)

        # How to define the Sample subtypes (and non-subtype)
        sample_subclass_basename = "SampleSubclass"
        sample_lines = [
            "class {basename}{index}(Sample):",
            "\tdef __init__(*args, **kwargs):",
            "\t\tsuper({basename}{index}, self).__init__(*args, **kwargs)",
        ]
        non_sample_class_lines = [
            "class NonSample(object):",
            "\tdef __init__(self):",
            "\t\tsuper(NonSample, self).__init__()",
        ]

        # We expect the subtype iff there's just one Sample subtype.
        if num_sample_subclasses == 1:
            exp_subtype_name = "{}0".format(sample_subclass_basename)
        else:
            exp_subtype_name = Sample.__name__

        # Fill in the class definition template lines.
        def populate_sample_lines(n_classes):
            return [
                [
                    sample_lines[0].format(
                        basename=sample_subclass_basename, index=class_index
                    ),
                    sample_lines[1],
                    sample_lines[2].format(
                        basename=sample_subclass_basename, index=class_index
                    ),
                ]
                for class_index in range(n_classes)
            ]

        # Determine the groups of lines to permute.
        class_lines_pool = populate_sample_lines(num_sample_subclasses)
        if decoy_class:
            class_lines_pool.append(non_sample_class_lines)

        # Subtype fetch is independent of class declaration order,
        # so validate each permutation.
        for lines_order in itertools.permutations(class_lines_pool):
            # Write out class declarations and invoke the function under test.
            _create_module(lines_by_class=lines_order, filepath=pipe_path)
            subtype = piface.fetch_sample_subtype(
                protocol=ATAC_PROTOCOL_NAME,
                strict_pipe_key=atac_pipe_name,
                full_pipe_path=pipe_path,
            )

            # Make the assertion on subtype name, getting additional
            # information about the module that we defined if there's failure.
            try:
                assert exp_subtype_name == subtype.__name__
            except AssertionError:
                with open(pipe_path, "r") as f:
                    print("PIPELINE MODULE LINES: {}".format("".join(f.readlines())))
                raise

    @pytest.mark.parametrize(argnames="subtype_name", argvalues=[Sample.__name__])
    def test_Sample_as_name(
        self,
        tmpdir,
        subtype_name,
        atac_pipe_name,
        subtypes_section_spec_type,
        atacseq_piface_data_with_subtypes,
    ):
        """A pipeline may redeclare Sample as a subtype name."""

        # General values for the test
        subtype_name = Sample.__name__
        pipe_path = os.path.join(tmpdir.strpath, atac_pipe_name)

        # Define the subtype in the pipeline module.
        lines = [
            "from looper import Sample\n",
            "class {}({}):\n".format(subtype_name, subtype_name),
            "\tdef __init__(self, *args, **kwargs):\n",
            "\t\tsuper({}, self).__init__(*args, **kwargs)\n".format(subtype_name),
        ]
        with open(pipe_path, "w") as pipe_module_file:
            for l in lines:
                pipe_module_file.write(l)

        conf_path = write_config_data(
            protomap={ATAC_PROTOCOL_NAME: atac_pipe_name},
            conf_data=atacseq_piface_data_with_subtypes,
            dirpath=tmpdir.strpath,
        )
        piface = PipelineInterface(conf_path)
        subtype = piface.fetch_sample_subtype(
            protocol=ATAC_PROTOCOL_NAME,
            strict_pipe_key=atac_pipe_name,
            full_pipe_path=pipe_path,
        )

        # Establish that subclass relationship is improper.
        assert issubclass(Sample, Sample)
        # Our subtype derives from base Sample...
        assert issubclass(subtype, Sample)
        # ...but not vice-versa.
        assert not issubclass(Sample, subtype)
        # And we retained the name.
        assert subtype.__name__ == Sample.__name__

    @pytest.mark.parametrize(argnames="subtype_name", argvalues=["NonSample"])
    @pytest.mark.parametrize(
        argnames="test_type", argvalues=["return_sample", "class_found"]
    )
    def test_subtype_is_not_Sample(
        self,
        tmpdir,
        atac_pipe_name,
        subtype_name,
        test_type,
        atacseq_piface_data_with_subtypes,
        subtypes_section_spec_type,
    ):
        """Subtype in interface but not in pipeline is exceptional."""

        pipe_path = os.path.join(tmpdir.strpath, atac_pipe_name)

        # Write out pipeline module file with non-Sample class definition.
        lines = _class_definition_lines(subtype_name, name_super_type="object")
        with open(pipe_path, "w") as pipe_module_file:
            pipe_module_file.write("{}\n\n".format(SAMPLE_IMPORT))
            for l in lines:
                pipe_module_file.write(l)

        # Create the PipelineInterface and do the test call.
        path_config_file = write_config_data(
            protomap={ATAC_PROTOCOL_NAME: atac_pipe_name},
            conf_data=atacseq_piface_data_with_subtypes,
            dirpath=tmpdir.strpath,
        )
        piface = PipelineInterface(path_config_file)
        with pytest.raises(ValueError):
            piface.fetch_sample_subtype(
                protocol=ATAC_PROTOCOL_NAME,
                strict_pipe_key=atac_pipe_name,
                full_pipe_path=pipe_path,
            )

    @pytest.mark.parametrize(argnames="subtype_name", argvalues=["irrelevant"])
    @pytest.mark.parametrize(
        argnames="decoy_class",
        argvalues=[False, True],
        ids=lambda decoy: " decoy = {} ".format(decoy),
    )
    def test_subtype_not_implemented(
        self,
        tmpdir,
        atac_pipe_name,
        subtype_name,
        decoy_class,
        atacseq_piface_data_with_subtypes,
        subtypes_section_spec_type,
    ):
        """Subtype that doesn't extend Sample isn't used."""
        # Create the pipeline module.
        pipe_path = os.path.join(tmpdir.strpath, atac_pipe_name)
        lines = _class_definition_lines("Decoy", "object") if decoy_class else []
        with open(pipe_path, "w") as modfile:
            modfile.write("{}\n\n".format(SAMPLE_IMPORT))
            for l in lines:
                modfile.write(l)
        conf_path = write_config_data(
            protomap={ATAC_PROTOCOL_NAME: atac_pipe_name},
            conf_data=atacseq_piface_data_with_subtypes,
            dirpath=tmpdir.strpath,
        )
        piface = PipelineInterface(conf_path)
        with pytest.raises(ValueError):
            piface.fetch_sample_subtype(
                protocol=ATAC_PROTOCOL_NAME,
                strict_pipe_key=atac_pipe_name,
                full_pipe_path=pipe_path,
            )

    @pytest.mark.parametrize(
        argnames="subtype_name", argvalues=["SubsampleA", "SubsampleB"]
    )
    def test_matches_sample_subtype(
        self, tmpdir, atac_pipe_name, subtype_name, atacseq_piface_data
    ):
        """Fetch of subtype is specific even from among multiple subtypes."""

        # Basic values
        pipe_path = os.path.join(tmpdir.strpath, atac_pipe_name)
        decoy_class = "Decoy"
        decoy_proto = "DECOY"

        # Update the PipelineInterface data and write it out.
        atacseq_piface_data[atac_pipe_name][SUBTYPES_KEY] = {
            ATAC_PROTOCOL_NAME: subtype_name,
            decoy_proto: decoy_class,
        }
        conf_path = write_config_data(
            protomap={ATAC_PROTOCOL_NAME: atac_pipe_name, decoy_proto: atac_pipe_name},
            conf_data=atacseq_piface_data,
            dirpath=tmpdir.strpath,
        )

        # Create the collection of definition lines for each class.
        legit_lines = _class_definition_lines(subtype_name, Sample.__name__)
        decoy_lines = _class_definition_lines(decoy_class, Sample.__name__)

        for lines_order in itertools.permutations([legit_lines, decoy_lines]):
            with open(pipe_path, "w") as pipe_mod_file:
                pipe_mod_file.write("{}\n\n".format(SAMPLE_IMPORT))
                for class_lines in lines_order:
                    for line in class_lines:
                        pipe_mod_file.write(line)
                    pipe_mod_file.write("\n\n")

            # We need the new pipeline module file in place before the
            # PipelineInterface is created.
            piface = PipelineInterface(conf_path)
            subtype = piface.fetch_sample_subtype(
                protocol=ATAC_PROTOCOL_NAME,
                strict_pipe_key=atac_pipe_name,
                full_pipe_path=pipe_path,
            )
            assert subtype_name == subtype.__name__

    @pytest.mark.parametrize(argnames="spec_type", argvalues=["single", "nested"])
    def test_subtypes_list(
        self, tmpdir, atac_pipe_name, atacseq_piface_data, spec_type
    ):
        """As singleton or within mapping, only 1 subtype allowed."""

        pipe_path = os.path.join(tmpdir.strpath, atac_pipe_name)

        # Define the classes, writing them in the pipeline module file.
        subtype_names = ["ArbitraryA", "PlaceholderB"]
        with open(pipe_path, "w") as pipe_module_file:
            pipe_module_file.write("{}\n\n".format(SAMPLE_IMPORT))
            for subtype_name in subtype_names:
                # Have the classes be Sample subtypes.
                for line in _class_definition_lines(
                    subtype_name, name_super_type=Sample.__name__
                ):
                    pipe_module_file.write(line)
                pipe_module_file.write("\n\n")

        # Update the PipelineInterface data.
        subtype_section = (
            subtype_names
            if spec_type == "single"
            else {ATAC_PROTOCOL_NAME: subtype_names}
        )
        atacseq_piface_data[atac_pipe_name][SUBTYPES_KEY] = subtype_section

        # Create the PipelineInterface.
        conf_path = write_config_data(
            protomap={ATAC_PROTOCOL_NAME: atac_pipe_name},
            conf_data=atacseq_piface_data,
            dirpath=tmpdir.strpath,
        )
        piface = PipelineInterface(conf_path)

        # We don't really care about exception type, just that one arises.
        with pytest.raises(Exception):
            piface.fetch_sample_subtype(
                protocol=ATAC_PROTOCOL_NAME,
                strict_pipe_key=atac_pipe_name,
                full_pipe_path=pipe_path,
            )

    @pytest.mark.parametrize(argnames="target", argvalues=["Leaf", "Middle"])
    @pytest.mark.parametrize(argnames="spec_type", argvalues=["single", "mapping"])
    def test_sample_grandchild(
        self, tmpdir, spec_type, target, atacseq_piface_data, atac_pipe_name
    ):
        """The subtype to be used can be a grandchild of Sample."""

        pipe_path = os.path.join(tmpdir.strpath, atac_pipe_name)
        intermediate_sample_subtype = "Middle"
        leaf_sample_subtype = "Leaf"

        intermediate_subtype_lines = _class_definition_lines(
            intermediate_sample_subtype, Sample.__name__
        )
        leaf_subtype_lines = _class_definition_lines(
            leaf_sample_subtype, intermediate_sample_subtype
        )
        with open(pipe_path, "w") as pipe_mod_file:
            pipe_mod_file.write("{}\n\n".format(SAMPLE_IMPORT))
            for l in intermediate_subtype_lines:
                pipe_mod_file.write(l)
            pipe_mod_file.write("\n\n")
            for l in leaf_subtype_lines:
                pipe_mod_file.write(l)

        atacseq_piface_data[atac_pipe_name][SUBTYPES_KEY] = (
            target if spec_type == "single" else {ATAC_PROTOCOL_NAME: target}
        )
        conf_path = write_config_data(
            protomap={ATAC_PROTOCOL_NAME: atac_pipe_name},
            conf_data=atacseq_piface_data,
            dirpath=tmpdir.strpath,
        )

        piface = PipelineInterface(conf_path)
        subtype = piface.fetch_sample_subtype(
            protocol=ATAC_PROTOCOL_NAME,
            strict_pipe_key=atac_pipe_name,
            full_pipe_path=pipe_path,
        )

        assert target == subtype.__name__

    @pytest.fixture(scope="function")
    def atacseq_piface_data_with_subtypes(
        self, request, atacseq_piface_data, atac_pipe_name
    ):
        """
        Provide test case with PipelineInterface data.

        :param pytest._pytest.fixtures.SubRequest request: test case
            requesting the parameterization
        :param Mapping atacseq_piface_data: the PipelineInterface data
        :param str atac_pipe_name: name for the pipeline
        :return Mapping: same as input, but with Sample subtype specification
            section mixed in
        """

        # Get the test case's parameterized values.
        spec_type = request.getfixturevalue("subtypes_section_spec_type")
        subtype_name = request.getfixturevalue("subtype_name")

        # Determine how to specify the subtype(s).
        if spec_type is str:
            section_value = subtype_name
        elif spec_type is dict:
            section_value = {ATAC_PROTOCOL_NAME: subtype_name}
        else:
            raise ValueError(
                "Unexpected subtype section specification type: " "{}".format(spec_type)
            )

        # Update and return the interface data.
        atacseq_piface_data[atac_pipe_name][SUBTYPES_KEY] = section_value
        return atacseq_piface_data


def _class_definition_lines(name, name_super_type):
    """Create lines that define a class."""
    return [
        "class {t}({st}):\n".format(t=name, st=name_super_type),
        "\tdef __init__(self, *args, **kwarggs):\n",
        "\t\tsuper({t}, self).__init__(*args, **kwargs)".format(
            t=name, st=name_super_type
        ),
    ]


def _create_module(lines_by_class, filepath):
    """
    Write out lines that will defined a module.

    :param Sequence[str] lines_by_class: lines that define a class
    :param str filepath: path to module file to create
    :return str: path to the module file written
    """
    lines = "\n\n".join(
        [SAMPLE_IMPORT] + ["\n".join(class_lines) for class_lines in lines_by_class]
    )
    with open(filepath, "w") as modfile:
        modfile.write("{}\n".format(lines))
    return filepath
