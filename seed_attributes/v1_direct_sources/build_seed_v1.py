"""Build the closed seed list v1 from three direct sources (no mapping to our own codebook):
 1. The Component Gallery (component.gallery/components, 60 components, alternate names, example counts), fetched 2026-10-26
 2. Open UI Component Name Matrix (open-ui.org/research/component-matrix; names per design system), fetched 2026-10-26
 3. Tailwind Plus marketing section categories (names from search-result summaries of tailwindcss.com/plus/ui-blocks/marketing, whose page is login-gated)
Writes component_gallery.csv, openui_matrix.csv, tailwind_plus_marketing.csv and seed_v1.csv in this folder. Run from the project root."""
import csv, re, collections, pathlib
D = pathlib.Path("seed_attributes/v1_direct_sources")
GAL = """Accordion|Arrow toggle;Collapse;Collapsible sections;Collapsible;Details;Disclosure;Expandable;Expander;ShowyHideyThing|101
Alert|Notification;Feedback;Message;Banner;Callout|108
Avatar||38
Badge|Tag;Label;Chip|123
Breadcrumbs|Breadcrumb trail|55
Button||118
Button group|Toolbar|35
Card|Tile|77
Carousel|Content slider|22
Checkbox||84
Color picker||18
Combobox|Autocomplete;Autosuggest|37
Date input||18
Datepicker|Calendar;Datetime picker|44
Drawer|Tray;Flyout;Sheet|38
Dropdown menu|Select menu|49
Empty state||16
Fieldset||32
File|Attachment;Download|6
File upload|File input;File uploader;Dropzone|32
Footer||19
Form||21
Header||38
Heading||29
Hero|Jumbotron;Banner|9
Icon||45
Image|Picture|29
Label|Form label|15
Link|Anchor;Hyperlink|64
List||67
Modal|Dialog;Popup;Modal window|82
Navigation|Nav;Menu|62
Pagination||48
Popover||50
Progress bar|Progress|40
Progress indicator|Progress tracker;Stepper;Steps;Timeline;Meter|38
Quote|Pull quote;Block quote|11
Radio button|Radio;Radio group|85
Rating||19
Rich text editor|RTE;wysiwyg editor|5
Search input|Search|30
Segmented control|Toggle button group|28
Select|Dropdown;Select input|82
Separator|Divider;Horizonal rule;Vertical rule|34
Skeleton|Skeleton loader|30
Skip link||14
Slider|Range input|38
Spinner|Loader;Loading|66
Stack||10
Stepper|Nudger;Quantity;Counter|20
Table||73
Tabs|Tabbed interface|80
Text input||72
Textarea|Textbox;Text box|52
Toast|Snackbar|41
Toggle|Switch;Lightswitch;Toggle button|60
Tooltip|Toggletip|74
Tree view||14
Video|Video player|15
Visually hidden|Screenreader only|11"""
OUI = {
"Ant Design":"Alert,Anchor,Autocomplete,Avatar,BackTop,Badge,Breadcrumb,Button,Calendar,Card,Carousel,Cascader,Checkbox,CheckboxGroup,Collapse,Comment,DatePicker,Description List,Divider,Drawer,Dropdown,Dropdown.Button,Empty,Form,Grid,Icon,Image,Input,InputNumber,Layout,List,Mentions,Menu,Message,Modal,Notification,PageHeader,Pagination,Paragraph,Popconfirm,Popover,Progress,Radio,Rate,Result,Select,Skeleton,Slider,Space,Spin,Statistic,Steps,Switch,Tabs,Table,Tag,Text,Timeline,TimePicker,Title,Tooltip,Transfer,Tree,TreeSelect,Typography,Upload,Affix",
"Atlaskit":"Avatar,Avatar group,Badge,Banner,Blanket,Breadcrumbs,Button,Calendar,Checkbox,Code,Comment,Datetime Picker,Drawer,Dropdown Menu,Droplist,Dynamic table,Empty state,Feedback collector,Field radio group,Field range,Field text,Field text area,Flag,Form,Global navigation,Grid,Icon,Inline dialog,Inline edit,Inline message,Logo,Lozenge,Menu,Modal dialog,Navigation,Onboarding,Page header,Pagination,Progress indicator,Progress tracker,Radio,Range,Right side panel,Section message,Select,Spinner,Tabs,Table tree,Tag,Tag group,Textarea,Textfield,Toggle,Tooltip,Tree",
"Auth0 Styleguide":"Alerts,Badges,Breadcrumb,Buttons,Cards,Footer,Forms,Header,Image,Jumbotron,Labels,Modals,Navs,Notifications,Phone Mockup,Showcase Tabs,Spinner,Stack Layout,Tables,Try Banner,UI Switch",
"Boosted":"Accordion,Alerts,Back to top,Badge,Breadcrumb,Buttons,Button group,Card,Carousel,Checkbox,Close button,Collapse,Dropdowns,File input,Footer,Img,List group,Modal,Navbar,Navs & tabs,Offcanvas,Pagination,Placeholders,Popovers,Progress,Quantity selector,Radios,Range,Scrollspy,Select,Spinners,Star rating,Stepped process,Sticker,Switches,Tables,Tags,Title bars,Toasts,Tooltips",
"Bootstrap":"Accordion,Alert,Badge,Breadcrumb,Buttons,Button group,Card,Carousel,Checkbox,Collapse,Dropdown,Flex,Forms,Img,InputGroup,List,Menu,Modal,Navs,Navbar,Pagination,Popover,Progress,Radio,Scrollspy,Select Menu,Spinners,Switch,Tables,Toasts,Tooltips",
"Carbon":"Accordion,Breadcrumb,Button,Checkbox,Code snippet,Content switcher,Data table,Date picker,Dropdown,File uploader,Form,Inline loading,Link,List,Loading,Modal,Multiselect,Number input,Overflow menu,Pagination,Progress indicator,Radio Button,Search,Select,Slider,Structured list,Tabs,Tag,Text input,Tile,Toast,Toggle,Tooltip,UI shell",
"Evergreen":"Alert,Autocomplete,Avatar,Badge,Button,Checkbox,Combobox,Corner Dialog,Dialog,Filepicker,Form Field,Menu,Pane,Pill,Popover,Radio,Search Input,Segmented Control,Select,Select Menu,Side Sheet,Spinner,Switch,Tabs,Table,Tag Input,Textarea,Text Input,Toaster,Tooltip",
"UI Fabric":"Breadcrumb,Button,Calendar,Callout,Checkbox,ChoiceGroup,Coachmark,ColorPicker,Combobox,CommandBar,ContextualMenu,DatePicker,DetailsList,Dialog,DocumentCard,Dropdown,Facepile,GroupedList,HoverCard,Icon,Image,Label,Link,Menu,MessageBar,Modal,Nav,Overlay,Panel,Persona,Pivot,ProgressIndicator,Rating,SearchBox,Separator,Shimmer,Slider,SpinButton,Spinner,Stack,TeachingBubble,Text,TextField,Toggle,Tooltip",
"FAST":"Accordion,Anchor,Badge,Breadcrumb,Button,Card,Checkbox,Combobox,Data Grid,Dialog,Divider,Flipper,Listbox,Menu,Number field,Progress,Progress ring,Radio,Radio group,Select,Skeleton,Slider,Switch,Tabs,Text area,Text field,Tooltip,Tree view",
"KoliBri":"Abbr,Accordion,Alert,Avatar,Badge,Breadcrumb,Button,Card,Combobox,Details,Dialog,Drawer,Form,Heading,Icon,Image,Link,Modal,Nav,Pagination,Progress,Quote,Select,SkipNav,Spin,SplitButton,Tabs,Textarea,Toolbar,Tree,InputCheckbox,InputColor,InputDate,InputEmail,InputFile,InputNumber,InputPassword,InputRadio,InputRange,InputText",
"Lightning":"Accordion,Activity Timeline,Alert,App Launcher,Avatar,Avatar Group,Badges,Brand Band,Breadcrumbs,Buttons,Button Groups,Button Icons,Cards,Carousel,Chat,Checkbox,Color Picker,Combobox,Data Tables,Datepickers,Datetime Picker,Drop Zone,Expandable Section,Feeds,Files,File Selector,Form Element,Global Header,Global Navigation,Grid,Icons,Illustration,Input,Map,Menu,Modal,Notification,Page Headers,Panels,Path,Picklist,Pills,Popovers,Progress Bar,Progress Indicator,Progress Ring,Radio Group,Rich Text Editor,Select,Slider,Spinners,Split View,Summary Detail,Tabs,Textarea,Tiles,Timepicker,Toast,Tooltip,Trees,Tree Grid,Vertical Navigation,Vertical Tabs,Welcome Mat",
"Lion":"Accordion,Button,Calendar,Checkbox Group,Collapsible,Combobox,Dialog,Drawer,Fieldset,Form,Icon,Input,Listbox,Pagination,Progress Indicator,Radio Group,Select,Steps,Switch,Tabs,Textarea,Tooltip",
"Material Components Web":"Badge,Buttons,Cards,Carousel,Checkbox,Chips,Data Tables,Dialog,Drawers,Floating Action Button,Form Fields,Grid Lists,Icon,Icon Buttons,Image List,Layout Grid,Linear Progress,Lists,Menu,Radio Buttons,Select,Sliders,Snackbar,Switches,Tabs,Text Field,Tooltip,Top App Bar,Typography",
"Oat":"Accordion,Alert,Badge,Breadcrumb,Button,Card,Dialog,Dropdown,Meter,Pagination,Progress,Sidebar,Skeleton,Spinner,Switch,Tabs,Table,Toast,Tooltip",
"Primer":"Autocomplete,Avatar,Button,Dropdown,Popover,TextInput,Toast,Tooltip",
"Semantic UI":"Accordion,Advertisement,Breadcrumb,Button,Card,Checkbox,Comment,Container,Dimmer,Divider,Dropdown,Embed,Feed,Flag,Form,Grid,Header,Icon,Image,Input,Item,Label,List,Loader,Menu,Message,Modal,Placeholder,Popup,Progress,Rail,Rating,Reveal,Search,Segment,Shape,Sidebar,Statistic,Step,Sticky,Tab,Table,Tooltip",
"Spectrum":"Action bar,Action button,Action group,Alert banner,Alert dialog,Avatar,Badge,Breadcrumbs,Button,Button group,Checkbox,Checkbox group,Close button,Code,Color area,Color slider,Color wheel,Combo box,Contextual help,Divider,Field label,Heading,Help text,In-line alert,Link,Menu,Meter,Picker,Popover,Progress bar,Progress circle,Radio Group,Rating,Side navigation,Slider,Status light,Swatch,Switch,Tabs,Tag,Text area,Text field,Toast,Tooltip,Tray,Tree view",
"Stardust UI":"Accordion,Alert,Attachment,Avatar,Button,Card,Chat,Checkbox,Dialog,Divider,Dropdown,Embed,Flex,Form,Grid,Header,Icon,Image,Input,Label,Layout,List,Loader,Menu,Popup,RadioGroup,Reaction,Segment,Slider,Status,Text,Toolbar,Tooltip,Tree,Video",
"USWDS":"Accordion,Alert,Banner,Breadcrumb,Button,Button Group,Card,Character Count,Checkbox,Collection,Combo Box,Date Picker,File Input,Footer,Header,Icon,Icon List,Identifier,In-page Navigation,Language Selector,Link,List,Modal,Pagination,Process List,Prose,Radio Buttons,Range Slider,Search,Select,Side Navigation,Site Alert,Step Indicator,Summary Box,Table,Tag,Text Input,Time Picker,Tooltip,Validation",
"WAI-ARIA":"Accordion,Alert,Alert and Message Dialogs,Breadcrumb,Button,Carousel,Checkbox,Combobox,Datepicker dialog,Dialog (Modal),Disclosure,Feed,Grid,Link,Listbox,Menu and Menubar,Menu Button,Meter,Radio Group,Slider,Spinbutton,Switch,Tabs,Table,Toolbar,Tooltip,Treegrid,Tree View",
"Web Platform (HTML)":"A,Audio,Button,Checkbox,Color,Datalist,Date,Details,Dialog,Email,File,Img,Label,Legend,Meter,Month,Nav,Number,Ol,Password,Picture,Progress,Radio,Range,Reset,Search,Select,Submit,Table,Telephone,Text,Time,Ul,URL,Video,Week"}
TW = ["Hero Sections","Feature Sections","CTA Sections","Pricing Sections","Testimonials","Bento Grids","Header Sections","Newsletter Sections","Stats Sections","Blog Sections","Contact Sections","Team Sections","Content Sections","Logo Clouds","FAQs","Footers"]
gal = [(r.split("|")[0], [x for x in r.split("|")[1].split(";") if x], int(r.split("|")[2])) for r in GAL.splitlines()]
with open(D / "component_gallery.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["component", "alternate_names", "examples"]); [w.writerow([n, "; ".join(a), e]) for n, a, e in gal]
with open(D / "openui_matrix.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["design_system", "name"]); [w.writerow([s, n]) for s, ns in OUI.items() for n in ns.split(",")]
with open(D / "tailwind_plus_marketing.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["section_category"]); [w.writerow([t]) for t in TW]
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", re.sub(r"([a-z])([A-Z])", r"\1 \2", s).lower().replace("-", " ")).strip()
sing = lambda s: re.sub(r"(?<=[^s])s$", "", s) if not s.endswith(("ss", "us")) else s
key = lambda s: sing(norm(s))
look = {}
for n, alts, e in gal: look[key(n)] = n
for n, alts, e in gal:
    for a in alts: look.setdefault(key(a), n)
EXTRA = {"dialog": "Modal", "modal dialog": "Modal", "dropdown": "Dropdown menu", "menu": "Dropdown menu", "nav": "Navigation", "navbar": "Navigation", "navs": "Navigation", "global navigation": "Navigation", "side navigation": "Navigation", "vertical navigation": "Navigation",
         "input": "Text input", "text field": "Text input", "textfield": "Text input", "field text": "Text input", "textfield": "Text input", "input text": "Text input", "field text area": "Textarea", "text area": "Textarea", "radios": "Radio button", "radio": "Radio button", "radio group": "Radio button", "img": "Image", "a": "Link", "anchor": "Link",
         "jumbotron": "Hero", "spin": "Spinner", "loader": "Spinner", "loading": "Spinner", "switch": "Toggle", "ui switch": "Toggle", "rate": "Rating", "star rating": "Rating", "star rating": "Rating", "steps": "Progress indicator", "step indicator": "Progress indicator", "progress": "Progress bar", "date picker": "Datepicker", "datepicker": "Datepicker", "calendar": "Datepicker",
         "tag": "Badge", "chip": "Badge", "pill": "Badge", "lozenge": "Badge", "snackbar": "Toast", "toaster": "Toast", "alert banner": "Alert", "message": "Alert", "notification": "Alert", "divider": "Separator", "separator": "Separator", "collapse": "Accordion", "details": "Accordion", "disclosure": "Accordion", "range": "Slider", "range slider": "Slider",
         "pagination": "Pagination", "tile": "Card", "ul": "List", "ol": "List", "list group": "List", "heading": "Heading", "title": "Heading", "picker": "Select", "dropdown field": "Select", "select menu": "Select", "file input": "File upload", "file selector": "File upload", "filepicker": "File upload", "drop zone": "File upload", "upload": "File upload", "file uploader": "File upload",
         "tab": "Tabs", "pivot": "Tabs", "tab bar": "Tabs", "table": "Table", "data table": "Table", "data grid": "Table", "details list": "Table", "tree": "Tree view", "tree grid": "Tree view", "popup": "Popover", "popovers": "Popover", "tooltip": "Tooltip", "quote": "Quote", "page header": "Header", "global header": "Header", "page headers": "Header", "title bars": "Header", "top app bar": "Header",
         "meter": "Progress indicator", "progress ring": "Progress indicator", "progress circle": "Progress indicator", "progress tracker": "Progress indicator", "activity timeline": "Progress indicator", "timeline": "Progress indicator", "search": "Search input", "search box": "Search input", "skeleton": "Skeleton", "shimmer": "Skeleton", "placeholder": "Skeleton", "empty": "Empty state", "result": "Empty state"}
for k, v in EXTRA.items(): look[key(k)] = v
cnt, raw = collections.defaultdict(set), collections.defaultdict(set)
for s, ns in OUI.items():
    for n in ns.split(","):
        c = look.get(key(n)); (cnt[c] if c else raw[key(n)]).add(s); 
        if not c: raw.setdefault(key(n), set()).add(s)
rows = []
for n, alts, e in gal:
    rows.append({"item": n, "kind": "component", "sources": "component_gallery" + ("+openui" if cnt.get(n) else ""), "alternate_names": "; ".join(alts), "gallery_examples": e, "openui_systems": len(cnt.get(n, ()))})
for k, ss in sorted(raw.items(), key=lambda kv: -len(kv[1])):
    if len(ss) >= 3: rows.append({"item": k, "kind": "component", "sources": "openui_only", "alternate_names": "", "gallery_examples": "", "openui_systems": len(ss)})
tw_match = {"Hero Sections": "Hero", "Header Sections": "Header", "Footers": "Footer", "Testimonials": "Quote"}
for t in TW: rows.append({"item": t, "kind": "page_section", "sources": "tailwind_plus" + ("+component_gallery(" + tw_match[t] + ")" if t in tw_match else ""), "alternate_names": "", "gallery_examples": "", "openui_systems": ""})
with open(D.parent / "seed_v1.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["item", "kind", "sources", "alternate_names", "gallery_examples", "openui_systems"]); w.writeheader(); w.writerows(rows)
print(len(rows), "items:", collections.Counter((r["kind"], r["sources"].split("+")[0]) for r in rows))
print("openui names not matched to a gallery component and named by >=3 systems:", [(r["item"], r["openui_systems"]) for r in rows if r["sources"] == "openui_only"])
print("openui names named by 1-2 systems and not matched (dropped):", sum(1 for k, s in raw.items() if len(s) < 3))
