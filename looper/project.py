""" Looper version of NGS project model. """

from collections import defaultdict
import logging
import os
import peppy
from peppy.utils import alpha_cased
from .protocol_interface import ProtocolInterface


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"



_LOGGER = logging.getLogger(__name__)



class Project(peppy.Project):
    """
    Looper-specific NGS Project.

    :param config_file: path to configuration file with data from
        which Project is to be built
    :type config_file: str
    :param subproject: name indicating subproject to use, optional
    :type subproject: str
    :param default_compute: path to default compute environment
        configuration data, optional
    :type default_compute: str

    """
    def __init__(self, config_file, subproject=None, **kwargs):
        super(Project, self).__init__(
                config_file, subproject=subproject, 
                no_environment_exception=RuntimeError,
                no_compute_exception=RuntimeError, **kwargs)
        self.interfaces_by_protocol = \
            process_pipeline_interfaces(self.metadata.pipelines_dir)


    @property
    def required_metadata(self):
        """ Which metadata attributes are required. """
        return ["output_dir"]


    @property
    def project_folders(self):
        """ Keys for paths to folders to ensure exist. """
        return ["output_dir", "results_subdir", "submission_subdir"]


    @staticmethod
    def infer_name(path_config_file):
        """
        Infer project name from config file path.
        
        The assumption is that the config file lives in a 'metadata' subfolder 
        within a folder with a name representative of the project.
        
        :param str path_config_file: path to the project's config file.
        :return str: inferred name for project.
        """
        import os
        metadata_folder_path = os.path.dirname(path_config_file)
        proj_root_path, _ = os.path.split(metadata_folder_path)
        _, proj_root_name = os.path.split(proj_root_path)
        return proj_root_name


def process_pipeline_interfaces(pipeline_interface_locations):
    """
    Create a ProtocolInterface for each pipeline location given.

    :param Iterable[str] pipeline_interface_locations: locations, each of
        which should be either a directory path or a filepath, that specifies
        pipeline interface and protocol mappings information. Each such file
        should be have a pipelines section and a protocol mappings section
        whereas each folder should have a file for each of those sections.
    :return Mapping[str, Iterable[ProtocolInterface]]: mapping from protocol
        name to interface(s) for which that protocol is mapped
    """
    interface_by_protocol = defaultdict(list)
    for pipe_iface_location in pipeline_interface_locations:
        if not os.path.exists(pipe_iface_location):
            _LOGGER.warn("Ignoring nonexistent pipeline interface "
                         "location: '%s'", pipe_iface_location)
            continue
        proto_iface = ProtocolInterface(pipe_iface_location)
        for proto_name in proto_iface.protomap:
            _LOGGER.log(5, "Adding protocol name: '%s'", proto_name)
            interface_by_protocol[alpha_cased(proto_name)].append(proto_iface)
    return interface_by_protocol
