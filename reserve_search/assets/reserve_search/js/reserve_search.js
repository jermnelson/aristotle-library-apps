function ChangeSearchArticlesText(btn_text) {
 $("#dbs").html(btn_text);
}

function OnSubmitForm() {
 var search_url = "";
 var search_char = $("#dbs").html().charAt(0);
 switch(search_char) {
  case 'C':
   search_url = search_url.concat("http://www.tiger.coloradocollege.edu/search/r", escape($('#searchArticleIcon').val()).replace(/%20/g, '+'));
   break;
  case 'I':
   search_url = search_url.concat("http://www.tiger.coloradocollege.edu/search/p", escape($('#searchArticleIcon').val()).replace(/%20/g, '+'));
 }
 $("#searchForm").attr("action", search_url);
 return true;
}
