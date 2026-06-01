
async function navigateTo(page){
   let url = new URLSearchParams(location.search)
    const header = document.querySelector("header")
    url.set("page", page)
    console.log(url.toString())
    switch (page) {
        case 'about':
            await loadPage('about');
            header.style.display = "none";
            break;
        case 'home':
            await loadPage('home');
            break;
        case 'sounds':
            await loadPage("bitcrusher")
            break;
        case 'gear':
            await loadComponent("catalog");
            break;
        case 'contact':
            await loadPage("contact");
            break;
        default:
            await loadPage('home');
    }
}

async function loadPage(comp) {
    try {
        const response = await fetch(`./comp/${comp}.html`);
        if (!response.ok) throw new Error(`Failed to load ${comp}.html`);
        const html = await response.text();
        document.querySelector("#body").innerHTML = html;
        // Extract and run script tags
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');


        doc.querySelectorAll('script').forEach(script => {
            const newScript = document.createElement('script');
            newScript.text = script.textContent;
            document.body.appendChild(newScript);
        });

    } catch (error) {
        console.error(error);
        document.body.innerHTML = `<p>Error loading ${comp} page.</p>`;
    }
}

async function loadComponent(comp, parent) {
    console.log("loading component",comp)
    let div = document.createElement("div")
    try {
        const response = await fetch(`./comp/${comp}.html`);
        if (!response.ok) throw new Error(`Failed to load ${comp}.html`);
        const html = await response.text();
        div.innerHTML = html;
        // Extract and run script tags
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');


        doc.querySelectorAll('script').forEach(script => {
            const newScript = document.createElement('script');
            newScript.text = script.textContent;
            div.appendChild(newScript);
        });

    } catch (error) {
        console.error(error);
        div.innerHTML = `<p>Error loading ${comp} page.</p>`;
    }
    parent.appendChild(div)
    return div
}

async function getCSVContents(local, remote) {
  try {
    let config = await fetch("./static/config.json").then(response => response.json());
    const csvData = config.debug ? await getCSVFromFile(local) : await getCSVFromGoogleSheet(remote);
    // console.log("got data", csvData)
    return csvData
  } catch (error) {
    console.error('Error fetching or parsing CSV:', error);
  }
}

function adjustFontSizeOnResize(item) {
  let on_desktop = window.innerWidth > 1000
  console.log("on_desktop: ", on_desktop)
  document.body.style.setProperty('--font_size_small', `${item.font_size_base*0.5}px`);
  document.body.style.setProperty('--font_size_base', `${item.font_size_base}px`);
  document.body.style.setProperty('--font_size_h1', `${item.font_size_base*2}px`);
  document.body.style.setProperty('--font_size_h2', `${Math.floor(item.font_size_base*1.5)}px`);
  document.body.style.setProperty('--font_size_h3', `${Math.floor(item.font_size_base*1.25)}px`);
  document.body.style.setProperty('--font_size_h4', `${item.font_size_base}px`);
  document.body.style.setProperty('--font_size_title', `${item.font_size_base*4}px`);
  if (on_desktop) {
    document.body.style.setProperty('--font_size_small', `${item.font_size_base}px`); 
    document.body.style.setProperty('--font_size_base', `${item.font_size_base*2}px`); 
    document.body.style.setProperty('--font_size_h1', `${item.font_size_base*4}px`);
    document.body.style.setProperty('--font_size_h2', `${item.font_size_base*3}px`);
    document.body.style.setProperty('--font_size_h3', `${Math.floor(item.font_size_base*2.5)}px`);
    document.body.style.setProperty('--font_size_h4', `${item.font_size_base*2}px`);
    document.body.style.setProperty('--font_size_title', `${item.font_size_base*4}px`);

  }
}


function buildPage(csvData) {
    let data = csvData
    console.log("building page")
    data.forEach(async (item) => {
      console.log("adding",item)

      if (item.component == "theme"){
          // for each key in item, set the corresponding css variable
          for (const [key, value] of Object.entries(item)) {
            console.log("setting",key,"to", value)
            if (key == "title") {
              document.title = value
            }
            document.body.style.setProperty(`--${key}`, value);
          }
          // adjust font size on resize
          window.onresize =() => {
            // alert("resize")
            adjustFontSizeOnResize(item)
          }

          adjustFontSizeOnResize(item)

          // document.body.style.setProperty('--background', item.bg_color);
          // document.body.style.setProperty('--text', item.text_color);
          // document.body.style.setProperty('--theme-primary', item.accent_color);
          // document.body.style.setProperty('--font_family_heading', item.font_family_heading);
          // document.body.style.setProperty('--font_family_body', item.font_family_body);
          

          // document.getElementById("logo").src = item.logo
          // document.getElementById("title").innerText = item.title
          return
      }
      let slot=document.createElement("div")
      slot.id = item.id
      slot.classList.add("slot")
      // console.log("loading component",item.component)
      if ("parent_id" in item && item.parent_id != null ){
        console.log("parent id", item.parent_id)
        document.getElementById(item.parent_id).appendChild(slot)
        await loadComponent(item.component, document.getElementById(slot.id)).then((comp) => {
          window.componentRegistry.get(item.component)(item);
        })
      }
      else {
        document.getElementById("body").appendChild(slot)
        await loadComponent(item.component, document.getElementById(slot.id)).then((comp) => {
          window.componentRegistry.get(item.component)(item);
        })
      }
        
    })
    let subfooter = document.createElement("div")
    subfooter.id = "subfooter"
    document.getElementById("body").appendChild(subfooter)
    subfooter.innerHTML = `<a id="power" href="https://innovainformationtechnologies.netlify.app/">Powered By Innova</a>`
    subfooter.style.color = "var(--primary_color)"
    subfooter.style.textAlign = "center"
    subfooter.style.margin = "2rem auto"
}


function extractSheetId(url) {
  const match = url.match(/\/d\/(.+?)\//);
  return match ? match[1] : null;
}

function parseCSV(csvText) {
  let sections = [];
  let currentSection = null;
  let headers = null;
  // Regex: Matches commas NOT inside double quotes
  const pattern = /,(?=(?:(?:[^"]*"){2})*[^"]*$)/;

  // Split into rows and clean up headers
  const rows = csvText.split(/\r?\n/);


  rows.forEach(row => {
    
    row = row.split(pattern).map(h => h.replace(/^"|"$/g, '').trim());
    if (row[0] == ""){ // reset on empty row
      currentSection = null;
      headers = null;
      return
    }
    // remove empty columns
    // console.log("row",row)
    row.forEach((col, i) => {
      // console.log("column ", col, ", ", col.length)
      if (col.length == 0) {
        // console.log("removing", col)
        row.splice(i, row.length - i);
      }
    })
    console.log("parsed row",row)
    if (row[0] == "component"){ // set headers
      // console.log(row[0], "set headers")
      headers = row
      return
    }

    if (headers != null && row != "") { // get rows
      currentSection = {};
      headers.forEach((h, i) => {
        currentSection[h] = row[i]
      });
      sections.push(currentSection);
      console.log("current section",currentSection)
    }
  })
  return sections
}

async function getCSVFromFile(filePath) {
  try {
    const response = await fetch(filePath);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${filePath}`);
    const csvText = await response.text();
    return parseCSV(csvText);
  } catch (err) {
    console.error("Critical System Failure: Ingestion Halted", err);
    return [];
  }
}

async function getCSVFromGoogleSheet(url, gid = '0') {
  try {
    const sheetId = extractSheetId(url);
    if (!sheetId) throw new Error(`Invalid Google Sheet URL: ${url}`);
    const fetchUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?tqx=out:csv&gid=${gid}`;
    const response = await fetch(fetchUrl);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${fetchUrl}`);
    const csvText = await response.text();
    return parseCSV(csvText);
  } catch (err) {
    console.error("Critical System Failure: Ingestion Halted", err);
    return [];
  }
}


window.messageBus = {
    listeners: {},
    on: function(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    },
    emit: function(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }
}

window.componentRegistry = {
    components: {},
    register: function(name, component) {
        this.components[name] = component;
    },
    get: function(name) {
        return this.components[name];
    }
}
const componentRegistry = window.componentRegistry
const messageBus = window.messageBus

export { getCSVContents, buildPage, loadComponent, componentRegistry, messageBus }