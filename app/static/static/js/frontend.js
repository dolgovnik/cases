document.addEventListener("DOMContentLoaded", sendSearchRequest); //for search request
document.addEventListener("DOMContentLoaded", checkSession);      //check is session exists after loading static index.html

var hot;
var error_code = 0;

//send search request, receive result, create href from case numbers and run building table
function sendSearchRequest(event){
  const form = document.querySelector('#search-form');
   form.addEventListener('submit', (event) => {
     event.preventDefault();
     if (error_code === 0){
       hot && hot.destroy();
     }
    const xhr = new XMLHttpRequest();
     xhr.open('POST', '/search', true)
     let data = JSON.stringify({'sreq': document.getElementsByTagName('input')[0].value});
     xhr.setRequestHeader("Content-Type", "application/json");
     xhr.onreadystatechange = function () {
       if (xhr.readyState === 4 && xhr.status === 200) {
             var json = JSON.parse(xhr.responseText);
             if (json['success'] === true){
               for (var i in json['result']){
                   json['result'][i][1] = '<a href="../case/00'+json['result'][i][1]+'" target="_blank">00'+json['result'][i][1]+'</a>';
               } 
               error_code = 0;
               buildTable(json['result']);
             } else {
               error_code = json['error_code'];
               showError(error_code);
             }
       }
     };
     xhr.send(data);
  })
}

//Builds table with HandsOnTable and data received from search request
function buildTable(data){
  const container = document.getElementById('result_table');
  container.innerHTML = ''
  hot = new Handsontable(container, {
    data: data,
    rowHeaders: true,
    colHeaders: ['Rank', 'CaseID', 'Product', 'Subject'],
    columns: [{readOnly: true}, {readOnly: true, renderer: 'html'}, {readOnly: true}, {readOnly: true}],
    columnSorting: true,
    filters: true,
    dropdownMenu: ['filter_by_condition', 'filter_action_bar'],
    height: 'auto',
    licenseKey: 'non-commercial-and-evaluation' // for non-commercial use only
  });
}

//Handle errors received from backend
function showError(error_code){
  if (error_code === 1){
    const container = document.getElementById('result_table');
    error_text = '<h1>No search results for this query :-(</h1>';
    container.innerHTML = error_text;
  }
  else if (error_code === 2){
    window.location.assign('/static/login.html');
  }
}

//Checking session in static index.html 
function checkSession(){
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/check_session', true)
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4 && xhr.status === 200) {
            var json = JSON.parse(xhr.responseText);
            if (json['success'] === false){
              error_code = json['error_code'];
              showError(error_code);
            }
      }
    };
    xhr.send();
}
