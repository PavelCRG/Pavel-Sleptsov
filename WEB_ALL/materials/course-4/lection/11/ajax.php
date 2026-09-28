<?php

if (isset($_REQUEST["q"])) {
    // Массив с кодами для РБ
    $a[] = "25 **--** life:)";
    $a[] = "33 **--** МТС";
    $a[] = "44 **--** Velcom";
    $a[] = "29 1--** Velcom";
    $a[] = "29 2--** МТС";
    $a[] = "29 3--** Velcom";
    $a[] = "29 5--** МТС";
    $a[] = "29 6--** Velcom";
    $a[] = "29 7--** МТС";
    $a[] = "29 8--** МТС";
    $a[] = "29 9--** Velcom";
    $a[] = "15 **--** Гродненская область";
    $a[] = "16 **--** Брестская область";
    $a[] = "17 **--** Минская область";
    $a[] = "21 **--** Витебская область";
    $a[] = "22 **--** Могилевская область";
    $a[] = "23 **--** Гомельская область";

    $q = $_REQUEST["q"];
    $hint = "";

    
    if ($q !== "") {
        $len = mb_strlen($q);
        foreach($a as $phone) {
          
            if(mb_stristr($q, mb_substr($phone, 0, $len))) {
                if($hint === "") $hint = $phone;
                else $hint .= "<br> $phone";
            }
        }
    }
    
   
    echo $hint === "" ? "Нет вариантов" : $hint;
    exit; 
}
?>

<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>AJAX Поиск по номеру телефона</title>
</head>
<body>


<script>
function showHint(str) {
    if(str.length == 0) {
        document.getElementById("txtHint").innerHTML = "";
        return;
    }
    else {
        let xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            
            if(this.readyState == 4 && this.status == 200) {
                document.getElementById("txtHint").innerHTML = this.responseText;
            }
        };
        
        xhr.open("GET", "?q=" + str, true);
        xhr.send();
    }
}
</script>

<p><b>Начните вводить номер вашего телефона, начиная с кода, в текстовое поле ниже:</b></p>

<form>
    телефон: 8-0 <input type="text" onkeyup="showHint(this.value)">
</form>

<p>Предлагаемые варианты: <span id="txtHint"></span></p>

</body>
</html>