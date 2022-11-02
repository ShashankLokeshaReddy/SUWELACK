import logging
import pandas as pd
import xml.etree.ElementTree as ET


def parse_XML(xml_file, df_cols):
    """Parse the input XML file and store the result in a pandas
    DataFrame with the given columns.

    The first element of df_cols is supposed to be the identifier
    variable, which is an attribute of each node element in the
    XML data; other features will be parsed from the text content
    of each sub-element.
    """

    xtree = ET.parse(xml_file)
    xroot = xtree.getroot()
    rows = []

    for node in xroot:
        res = []
        res.append(node.attrib.get(df_cols[0]))
        for el in df_cols[1:]:
            if node is not None and node.find(el) is not None:
                res.append(node.find(el).text)
            else:
                res.append(None)
        rows.append({df_cols[i]: res[i]
                     for i, _ in enumerate(df_cols)})

    out_df = pd.DataFrame(rows, columns=df_cols)

    return out_df


XMLtree = ET.parse('data/T904.xml')
DataRoot = XMLtree.getroot()
T904columns = ["name", "number", "groupnumber"]
rows = []
for tags in DataRoot.findall('T904_Kostenstellen'):
    Number = tags.find('T904_NR').text
    Name = tags.find('T904_Bez').text
    GroupNumber = tags.find('T904_GruppeNr').text
    rows.append({"name": Name, "number": Number,
                 "groupnumber": GroupNumber})
dataframeT904 = pd.DataFrame(rows, columns=T904columns)


logging.info("dataframeT904 read successful")

# Access terminal number from config
XMLtree = ET.parse('data/X998.xml')
DataRoot = XMLtree.getroot()
for tags in DataRoot.findall('X998_ConfigTerm'):
    X998_GrpPlatz = tags.find('X998_GrpPlatz').text

logging.info("Arbeitsplätze respective of %s" %(X998_GrpPlatz))
"""
XML T910  --> Vorname, name and passcode

"""
dataframeT910= parse_XML("data/T910.xml ", ["T910_Nr", "T910_Name", "T910_Vorname", "T910_Aktiv",
                                            "T910_Kst", "T910_Platz", "T910_KstK", "T910_Zuordnung", "T910_Entlohnung",
                                            "T910_TermRecht", "T910_Zeitmodell", "T910_Aenderung"])
logging.info("dataframeT910 read successful")


"""
XML T912  --> username, personalnumber and bez
"""
dataframeT912 = parse_XML("data/T912.xml", ["T912_FirmaNR", "T912_Nr", "T912_PersNr", "T912_Aenderung",
                                           "T912_Anlage", "T912_User"])
logging.info("dataframeT912 read successful")


"""
XML T905  --> username, personalnumber and bez
"""

XMLtree = ET.parse('data/T905.xml')
DataRoot = XMLtree.getroot()

arbeitsplatzlist = []
for tags in DataRoot.findall('T905_ArbMasch'):
    arbeitsplatz = tags.find('T905_Bez').text
    arbeitsplatzlist.append(arbeitsplatz)

#print(len(arbeitsplatzlist))
logging.info("dataframeT905 read successful")
"""
To print and display the Dataframes, uncomment the code below:
"""
#print(arbeitsplatzlist)
#print(dataframeT912)
#print(dataframeT910)
#print(dataframeT904)
