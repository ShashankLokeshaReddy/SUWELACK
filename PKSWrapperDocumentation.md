**def authenticate()**

"In order to authenticate user, user passes a userID and
the system fetches the details of the user respective to that userID"

**input:** 

int:userID

**output:** 

var:username

int:personnalnummber

int:FRNummer

var:gruppe

**Source:** [DLL,DB,XML]

### **No_button_selected**
**def identify_number("number")**

**input:**
var: number

**output:**
feedback:

kommt / geht / wechselbuchung / wechselbuchung_GKDialog / wechselbuchung_MengeDialog / auftragsbuchung / auftragsbuchung_GKdialog / auftragsbuchung_MengeDialog

**Source:** [DLL]

### **Arbeitsplatz**

**def get_list("arbeitsplatz")**

**input:**

var:arbeitsplatz

**output:**

list: arbeitplatz items e.g: 
"Eckpassstücke","Blenderzuschnitt",
"Muldenprofit"

**Source:** [DLL,DB,XML]


**def set_arbeitsplatz("arbeitsplatz,userID,
username,timestamp")**

**input:** 

var:username

int:userID

var:timestamp

var:arbeitsplatz

**output:**

feedback:

operation status:

successful/unsuccessful

**Source:** [DLL,DB,XML]

### **Gemeinkosten**

**def get_list("gemeinkosten")**

**input:**

var:gemeinkosten

**output:**

list: gemeinkosten items e.g: 
"Maschineninstellung","Reparatur","Muldenprofit","Entwicklung"

**Source:** [DLL,DB,XML]

### **Bereicht Drucken**

**def get_list("arbeitsplatzgruppe")**

**input:**

var:arbeitsplatzgruppe

**output:**



list: Arbeitsplatz Gruppe e.g: 
"Frontenlager","Verschiedenes(bundes)","Lehrwerkstatt","AV(Bunde)"

**Source:** [DLL,DB,XML]

### **Auftragsbuchung**

**def get_list("PrNr")**

"Gets a list of Personal Number of all registered users"

**input:**

int:PrNr

**output:**

list: Personal Number list

**Source:** [DLL,DB,XML]

**get_list("FrNr")**

"Gets a list of FR Number of all registered users"

**input:**

int:FrNr

**output:**

list: FR Number list

**Source:** [DLL,DB,XML]

### **Auftragsbuchung**

**def auftragsbuchung("")**

**input:**

var:buchungstag

var:arbeitsplatz

int:personalNumber

int:FAnumber

var:dauer

var:kurztext

**output:**

operation status: successful/unsuccessful

**Source:** [DLL,DB,XML]

### **Gruppenbuchung**

**def gruppenbuchung("")**


**input:**

var:buchungstag

int:FAnumber

var:dauer

var:kurztext

**output:**

operation status: successful/unsuccessful

**Source:** [DLL,DB,XML]

### **Fertigungsauftrag Erfassen**

**def get_fertigungsauftrags()**

input:

output: 

Entire table of Fertigungauftrags

**def update_fertigungauftrags():**

"Update entries in the table of Auftragsbuchung"

**input:**

float:gesamt

var:mengeIst

var:mengeAus

**output:**

operation status: successful/unsuccessful

**Source:** [DLL,DB,XML]

### **Gemeinkosten Äandern**

**def get_gemeinkosten()**

"Fetch and display Gemeinkosten table"
**input:**

**output:** 

Entire table of Gemeinkosten

**Source:** [DLL,DB,XML]

**def update_gemeinkosten():**

"Update entries in the table of Auftragsbuchung"

**input:**


**output:**

operation status: successful/unsuccessful

**Source:** [DLL,DB,XML]

###### **Status Table**

**def get_status()**

"Fetch and display Status table"

**input:**

**output:** 

"Entire table of Current Status of Employees"

**Source:** [DLL,DB,XML]
