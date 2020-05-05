// Variables
var topLevelItem = {};


// API urls
var baseURL = "https://api.guildwars2.com/v2/";
var languageAPI = "?lang=en";


function start(){
    itemIds = 76614;
    getItemObj(itemIds);

}

function getItemObj(itemId){
    url = baseURL+"items/"+itemId+languageAPI;
    topLevelItem.id=itemId;

    let request = new XMLHttpRequest();
    request.open('GET', url, true);
    request.onload = function() {
        if (request.status >= 200 && request.status < 400) {
            item = JSON.parse(this.response);
            checkRecipe(item.id);
        } else {
            console.log("Error during API call: getItemObj(), itemId = "+itemId);
        }
    };
    request.send();
}

function checkRecipe(itemId){
    url = baseURL+"recipes/search?output="+itemId;
    let request = new XMLHttpRequest();
    request.open('GET', url, true);
    request.onload = function() {
        if (request.status >= 200 && request.status < 400) {
            recipes = (JSON.parse(this.response));
            if(recipes.length>0) {
                recipes.forEach(e => getRecipeComponents(e))
            }
        } else {
            console.log("Error during API call: checkRecipe(), itemId = "+itemId);
        }
    };
    request.send();
}

function getRecipeComponents(recipeId){
    url = baseURL+"recipes/"+recipeId;
    let request = new XMLHttpRequest();
    request.open('GET', url, true);
    request.onload = function() {
        if (request.status >= 200 && request.status < 400) {
            recipe = (JSON.parse(this.response));
            topLevelItem.recipe=recipe;
            console.log(recipe);
            //stuck here, recursion for all ingredients with price check
            renderItem(item, recipe)
        } else {
            console.log("Error during API call: getRecipeComponents(), recipeId = "+recipeId);
        }
    };
    request.send();
}

function getIngredientObj(itemId){

}

function checkItemPrice(itemId){

}


function renderItem(item, recipe){
    document.write('<div>');
    document.write('<img src="'+item.icon+'"/>');
    document.write('<h4>'+item.name+'</h4>');
    recipe.ingredients.forEach(e=>document.write('<p>'+e.item_id+': '+e.count+'</p>'));
    document.write('</div>');
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