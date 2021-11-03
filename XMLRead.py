import xml.etree.ElementTree as ET
mytree = ET.parse('data/T904.xml')
DataRoot = mytree.getroot()
#for x in DataRoot[0]:
#     print(x.tag, x.attrib)
print("Number\t\tGroupNumber\t\tName")
for tags in DataRoot.findall('T904_Kostenstellen'):
    Number =tags.find('T904_NR').text
    Name = tags.find('T904_Bez').text
    GroupNumber = tags.find('T904_GruppeNr').text
    print(Number +"\t\t",GroupNumber +"\t\t\t",Name)