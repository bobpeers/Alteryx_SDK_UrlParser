import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et
from urllib.parse import urlparse, parse_qs
import json

class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        # Default properties
        self.n_tool_id: int = n_tool_id
        self.alteryx_engine: Sdk.AlteryxEngine = alteryx_engine
        self.output_anchor_mgr: Sdk.OutputAnchorManager = output_anchor_mgr

        # Custom properties
        self.url: str = None
        self.is_initialized = True
        
        self.input: IncomingInterface = None
        self.output: Sdk.OutputAnchor = None

    def pi_init(self, str_xml: str):
        # Getting the dataName data property from the Gui.html
        self.url = Et.fromstring(str_xml).find('url').text if 'url' in str_xml else None

        # Validity checks.
        if self.url is None:
            self.display_error_msg('URL field cannot be empty.')

        # Getting the output anchor from Config.xml by the output connection name
        self.output = self.output_anchor_mgr.get_output_anchor('Output')

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        self.input = IncomingInterface(self)
        return self.input

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return True

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, 'Missing Incoming Connection.')
        return False

    def pi_close(self, b_has_errors: bool):
        self.output.assert_close()

    def display_error_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, msg_string)
        self.is_initialized = False

    def display_info(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.info, msg_string)


class IncomingInterface:
    def __init__(self, parent: AyxPlugin):
        # Default properties
        self.parent: AyxPlugin = parent

        # Custom properties
        self.record_copier: Sdk.RecordCopier = None
        self.record_creator: Sdk.RecordCreator = None
        self.OutputField: Sdk.Field = None
        self.SourceField: Sdk.Field = None


    def ii_init(self, record_info_in: Sdk.RecordInfo) -> bool:
        # Make sure the user provided a field to parse
        if self.parent.url is None:
            self.parent.display_error_msg('Select a source field')
            return False
            
        # Get information about the source path field
        self.SourceField = record_info_in.get_field_by_name(self.parent.url)
        #match_field_type: Sdk.FieldType = self.SourceField.type
        #match_field_size: int = self.SourceField.size

        # Returns a new, empty RecordCreator object that is identical to record_info_in.
        self.record_info_out = record_info_in.clone()

        #output field config
        self.fields = [['protocol', Sdk.FieldType.string, 20],
                    ['net_location', Sdk.FieldType.string, 100],
                    ['path', Sdk.FieldType.string, 100],
                    ['query', Sdk.FieldType.string, 100],
                    ['parsed_query', Sdk.FieldType.string, 100],
                    ['fragment', Sdk.FieldType.string, 100],
                    ['hostname', Sdk.FieldType.string, 100],
                    ['port', Sdk.FieldType.int32,10]]

        self.outRecords = []
        # Adds field to record with specified name and output type.
        for name, dtype, size in self.fields:
            self.outRecords.append(self.record_info_out.add_field(name, dtype, size))

        # Lets the downstream tools know what the outgoing record metadata will look like
        self.parent.output.init(self.record_info_out)

        # Creating a new, empty record creator based on record_info_out's record layout.
        self.record_creator = self.record_info_out.construct_record_creator()

        # Instantiate a new instance of the RecordCopier class.
        self.record_copier = Sdk.RecordCopier(self.record_info_out, record_info_in)

        # Map each column of the input to where we want in the output.
        for index in range(record_info_in.num_fields):
            # Adding a field index mapping.
            self.record_copier.add(index, index)

        # Let record copier know that all field mappings have been added.
        self.record_copier.done_adding()

        return True


    def ii_push_record(self, in_record: Sdk.RecordRef) -> bool:

        if not self.parent.is_initialized:
            return False

        # Copy the data from the incoming record into the outgoing record.
        self.record_creator.reset()
        self.record_copier.copy(self.record_creator, in_record)

        # Get the text to parse and set the matches counter
        source: str = self.SourceField.get_as_string(in_record)


        if self.parent.alteryx_engine.get_init_var(self.parent.n_tool_id, 'UpdateOnly') == 'True':
            return False
        
        parsed = urlparse(source, allow_fragments=True)

        # Build output record

        self.outRecords[0].set_from_string(self.record_creator, parsed.scheme)
        self.outRecords[1].set_from_string(self.record_creator, parsed.netloc)
        self.outRecords[2].set_from_string(self.record_creator, parsed.path)
        self.outRecords[3].set_from_string(self.record_creator, parsed.query)
        self.outRecords[4].set_from_string(self.record_creator, json.dumps(parse_qs(parsed.query)))
        self.outRecords[5].set_from_string(self.record_creator, parsed.fragment)
        self.outRecords[6].set_from_string(self.record_creator, parsed.hostname if not parsed.hostname is None else '')
        if parsed.port is None:
            self.outRecords[7].set_null(self.record_creator)
        else:
            self.outRecords[7].set_from_int32(self.record_creator, parsed.port)

        out_record = self.record_creator.finalize_record()
        self.parent.output.push_record(out_record)
        
        return True

    def ii_update_progress(self, d_percent: float):
        # Inform the Alteryx engine of the tool's progress.
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)

        # Inform the outgoing connections of the tool's progress.
        self.parent.output.update_progress(d_percent)

    def ii_close(self):
        self.parent.display_info(f'Parsing complete')
        # Close outgoing connections.
        self.parent.output.close()
