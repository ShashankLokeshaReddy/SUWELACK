**def authenticate(userID)**

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
**def identify_number(number)**

"When a number is entered into the text field of the home screen, we need to identify whether it is a personalnumber or FA-number, and if the person is alredy signed in for the current day and has open bookings (fa or gk). Therefore we need the feedback of the function in order to present the next page. In case of kommt we need to move to the arbeitsplatz selection page. In case of geht we need an optional dialog box checking if the person really wants to log out. In case of wechselbuchung we do not have any open booking and can move to the arbeitsplatz selection page. ..."

**input:**
var: number

**output:**
feedback:

kommt / geht / wechselbuchung / wechselbuchung_GKDialog / wechselbuchung_MengeDialog / auftragsbuchung / auftragsbuchung_GKDialog / auftragsbuchung_MengeDialog

**Source:** [DLL]

### **Arbeitsplatz**

**def get_list_arbeitsplatz()**

**input:**

var:arbeitsplatz

**output:**

list: arbeitplatz items e.g: 
"Eckpassstücke","Blenderzuschnitt",
"Muldenprofit"

**Source:** [XML]


**def set_arbeitsplatz(arbeitsplatz,userID,
username,timestamp)**

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
