function ChangeSearchArticlesText(btn_text) {
 $("#dbs").html(btn_text);
}

function OnSubmitForm() {
 var search_url = "";
 var search_char = $("#dbs").html().charAt(0);
 switch(search_char) {
  case 'A':
   search_url = search_url.concat("http://0-search.ebscohost.com.tiger.coloradocollege.edu:80/login.aspx%3Fdirect=true&db=a9h&bquery=", escape($('#searchArticleIcon').val()).replace(/%20/g, '+'), "&type=1&site=ehost-live");
   break;
  case 'G':
   search_url = search_url.concat("http://0-scholar.google.com.tiger.coloradocollege.edu/scholar%3Fq=", escape($('#searchArticleIcon').val()).replace(/%20/g, '+'));
   break;
  case 'J':
   search_url = search_url.concat("http://0-www.jstor.org.tiger.coloradocollege.edu/action/doBasicSearch%3FQuery=", escape($('#searchArticleIcon').val()).replace(/%20/g, '+'), "&wc=on&acc=on");
 }
 $("#searchForm").attr("action", search_url);
 return true;
}
