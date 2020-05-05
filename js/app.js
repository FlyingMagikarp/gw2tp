var baseURL = "https://api.guildwars2.com/v2/";
var languageAPI = "?lang=en";

var mainItem = {};

async function start(value){
    mainItem = await createObjectFromId(value);






    console.log(mainItem);
}

async function asyncForEach(array, callback) {
    for (let index = 0; index < array.length; index++) {
        await callback(array[index], index, array);
    }
}

async function createIngredientObjects(rootItem){
    if(rootItem.ingredients !== 'FINAL') {
        asyncForEach(rootItem.ingredients, async (element) => {
            element.itemObject = await createObjectFromId(element.item_id);
        });
    }
}

async function createObjectFromId(itemId){
    let item = {};
    item.id = itemId;

    const itemObj = await getItemObject(item.id);

    item.icon = itemObj.icon;

    const mainItemPrices = await getPrices(item.id);

    item.buyPrice = mainItemPrices.buys.unit_price;
    item.sellPrice = mainItemPrices.sells.unit_price;

    const recipes = await getAllRecipesId(item.id, {});

    item.recipes = recipes;

    if(typeof item.recipes !== "undefined" && item.recipes.length > 0) {
        const mainRecipe = await getRecipeContent(recipes[0]);

        item.outputAmount = mainRecipe.output_item_count;
        item.ingredients = mainRecipe.ingredients;
    } else {
        item.outputAmount = 1;
        item.ingredients = 'FINAL';
    }

    await createIngredientObjects(item);

    return item;
}

async function getItemObject(itemId) {
    url = baseURL + "items/" + itemId + languageAPI;
    const response = await fetch(url, {});
    if (response.ok){
        return await response.json();
    } else {
        console.log("Error during API call: "+response.status+" At getItemObject() itemId: "+itemId);
    }
}

async function getAllRecipesId(itemId){
    url = baseURL+"recipes/search?output="+itemId;
    const response = await fetch(url, {});
    if (response.ok){
        return await response.json();
    } else {
        console.log("Error during API call: "+response.status+" At getAllRecipesId() itemId: "+itemId);
    }
}

async function getRecipeContent(recipeId){
    url = baseURL+"recipes/"+recipeId;
    const response = await fetch(url, {});

    if (response.ok){
        return await response.json();
    } else {
        console.log("Error during API call: "+response.status+" At getRecipeContent() recipeId: "+recipeId);
    }
}




async function getPrices(itemId){
    url = baseURL+"commerce/prices/"+itemId;
    const response = await fetch(url, {});
    if (response.ok){
        return await response.json();
    } else {
        console.log("Error during API call: "+response.status+" At getAllRecipesId() itemId: "+itemId);
    }
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