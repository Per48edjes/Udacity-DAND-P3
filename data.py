# Import dependencies
import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import cerberus
import schema
import audit


OSM_PATH = "SF_extract.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []

    # Counter initialize for 'nd' tags
    i = 0

    # 'Node' attributes
    if element.tag == 'node':
        flag = "node"
        for a in element.attrib:
            if a in NODE_FIELDS:
                node_attribs[a] = element.attrib[a]
        
    # 'Way' attributes
    elif element.tag == 'way':
        flag = "way"
        for w in element.attrib:
            if w in WAY_FIELDS:
                way_attribs[w] = element.attrib[w]        

    # Children tags
    for child in element:
        
        # 'Ways_nodes' list
        if child.tag == "nd":
            ways_node_dict = {}
            ways_node_dict['id'] = way_attribs['id']            
            ways_node_dict['node_id'] = child.attrib['ref']
            ways_node_dict['position'] = i
            i += 1
            way_nodes.append(ways_node_dict)
        
        # Create dictionary for each 'tag' tag
        if child.tag == "tag":
            if PROBLEMCHARS.match(child.attrib["k"]):
                continue
            
            # Dictionary of 'tag' tags to skip
            erroneous_tags = {"phone": "fire"}
            if (child.attrib["k"] in erroneous_tags) and (child.attrib["v"] == erroneous_tags[child.attrib["k"]]):
                continue
            
            else:
                child_dict = {}
                if flag == "node":
                    child_dict['id'] = node_attribs['id']
                if flag == "way":
                    child_dict['id'] = way_attribs['id']
                
                for k, v in child.attrib.items():
                    if k == 'k':    
                        if LOWER_COLON.match(v):
                            child_dict["key"] = v[v.find(':')+1:]
                            child_dict["type"] = v[:v.find(':')]
                        else: 
                            child_dict["key"] = v
                            child_dict["type"] = default_tag_type
                    
                    if k == 'v':

                        '''CLEANING DATA FOR EXPORT TO CSV''' 
                        
                        # Cleaning street names
                        if child_dict["key"] == "street": 
                            child_dict["value"] = audit.update_street_name(v)

                        # Cleaning phone numbers
                        elif child_dict["key"] == "phone":
                            child_dict["value"] = audit.update_phoneNum(v)

                        # Cleaning zip codes 
                        elif child_dict["key"] == "postcode":
                            child_dict["value"] = audit.update_zipcode(v)

                        # If not identified for cleaning, as-is value is returned
                        else:
                            child_dict["value"] = v

                tags.append(child_dict)

    # Return data structure
    if flag == "node":
        return {'node': node_attribs, 'node_tags': tags}
    elif flag == "way":
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


# EXECUTION OF SCRIPT
if __name__ == '__main__':
    process_map(OSM_PATH, validate=False)
    
