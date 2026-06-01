let config = await fetch("./static/config.json").then(response => response.json());
let getCSVContents, buildPage

if (config.debug) {
  await import("./scripts/util.js").then(module => {
    getCSVContents = module.getCSVContents;
    buildPage = module.buildPage
  });
} else {
  await import ("https://cdn.jsdelivr.net/gh/innovainformationtechnologies/sheetsite-util@main/util.js").then(module => {
    getCSVContents = module.getCSVContents;
    buildPage = module.buildPage
  });
  
}

let data = [];


console.log(getCSVContents)

await getCSVContents("./static/sheet.csv", null).then(data => {
  console.log(data)
  buildPage(data);
});
