function ChangeSearchBookText(btn_text) {
 $("#searchby").html(btn_text);
 $("#searchby").val(btn_text);
 var search_char = btn_text.charAt(7);
 switch(search_char) {
  case 'A':
   $('#search-type').val("author_search");
   break;
  case 'J':
   $('#search-type').val("title_search");
   break;
  case 'K':
   $('#search-type').val("search");
   break;
  case 'S':
   $('#search-type').val("subject_search");
   break;
  case 'T':
   $('#search-type').val("title_search");
 }
}
