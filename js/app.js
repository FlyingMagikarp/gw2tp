// Variables
var items = [];


// API urls
var baseURL = "https://api.guildwars2.com/v2/";
var languageAPI = "?lang=en";


function start(){
    itemIds = 76614;
    getItemObj(itemIds);

}

function getItemObj(itemid){
    url = baseURL+"items/"+itemid+languageAPI;

    var request = new XMLHttpRequest();
    request.open('GET', url, true);
    request.onload = function() {
        if (request.status >= 200 && request.status < 400) {
            item = JSON.parse(this.response);
            checkRecipe(item.id);
        } else {
            console.log("Error during API call: getItemObj(), itemid = "+itemid);
        }
    };
    request.send();
}

function checkRecipe(itemId){
    url = baseURL+"recipes/search?output="+itemId;
    var request = new XMLHttpRequest();
    request.open('GET', url, true);
    request.onload = function() {
        recipes = (JSON.parse(this.response));
        recipes.forEach(e=>getRecipeComponents(e))
    };
    request.send();
}

function getRecipeComponents(recipeId){
    url = baseURL+"recipes/"+recipeId;
    var request = new XMLHttpRequest();
    request.open('GET', url, true);
    request.onload = function() {
        recipe = (JSON.parse(this.response));

    };
    request.send();
}


function priceFormatter(value) {
    if(typeof value==='undefined'){value=0}
    value=''+value;
    len = value.length;
    if(len<3){
        copper = value;
        silver = 0;
        gold = 0;
    } else if (len<5){
        copper = value.substr(len-2);
        silver = value.substr(0,len-2);
        gold = 0;
    } else {
        copper = value.substr(len-2);
        silver = value.substr(len-4,2);
        gold = value.substr(0,len-4);
    }
    price={};
    price.copper = parseInt(copper);
    price.silver = parseInt(silver);
    price.gold = parseInt(gold);

    return price;
}