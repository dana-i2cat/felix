"use strict";

var platform8 = new dtjava.Platform({javafx: '8+', jvm: '1.8+'});
var platform7 = new dtjava.Platform({javafx: '2.2+'});

//used to store for which id the dialog is displayed
var dialog_id = 'experimenter';
//initialization of the dialog
$(function () {
    $("#java7Dialog").dialog({
        autoOpen: false,
        buttons: [
            {
                text: "Upgrade to Java 8",
                click: function () {
                    window.open("http://java.com/en/download/");
                    $(this).dialog("close");
                    // NB: Google Analytics code can be removed
                    //ga('send', 'event', 'webstart', 'click', 'install_java');
                }
            },
            {
                text: "Launch jFed 5.3.2",
                click: function () {
                    dtjava.launch({url: java7_jnlp[dialog_id]}, platform7, {});
                    $(this).dialog("close");
                    //ga('send', 'event', 'webstart', 'start', 'java7');
                }
            },
            {
                text: "Close",
                click: function () {
                    $(this).dialog("close");
                    //ga('send', 'event', 'webstart', 'click', 'close');
                }
            }
        ],
        width: 500
    });

    $("#noJavaDialog").dialog({
        autoOpen: false,
        buttons: [
            {
                text: "Install Java",
                click: function () {
                    window.open("http://java.com/en/download/");
                    $(this).dialog("close");
                    //ga('send', 'event', 'webstart', 'click', 'install_java');
                }
            },
            {
                text: "Close",
                click: function () {
                    $(this).dialog("close");
                    //ga('send', 'event', 'webstart', 'click', 'close');
                }
            }
        ],
        width: 500
    });
});


function launchjFed(id) {
    //ga('send', 'event', 'button', 'click', 'webstart');

    var result = dtjava.validate(platform8);

    if (result !== null) {
        if (dtjava.validate(platform7) !== null) {
            //no java 7 or 8 detected: suggest installing Java
            //$("#versioninfo_nojava").text("Version-info: " + result.toString());
            $("#noJavaDialog").dialog("open");
            //ga('send', 'event', 'webstart', 'detected', 'nojava');
        } else {
            //Java 7 detected, suggest upgrading or using older version
            //$("#versioninfo").text("Version-info: " + result.toString());
            dialog_id = id;
            $("#java7Dialog").dialog("open");
            //ga('send', 'event', 'webstart', 'detected', 'java7');
        }
    } else {
        //Java 8 detected, launch latest jFed version!
        dtjava.launch({url: java8_jnlp[id]}, platform8, {});
        //ga('send', 'event', 'webstart', 'start', 'java8');
    }

    return false;
}

function launchjFedBeta(url) {
    //ga('send', 'event', 'button', 'click', 'webstart');

    var result = dtjava.validate(platform8);

    if (result !== null) {
        if (dtjava.validate(platform7) !== null) {
            //no java 7 or 8 detected: suggest installing Java
            //$("#versioninfo_nojava").text("Version-info: " + result.toString());
            $("#noJavaDialog").dialog("open");
            //ga('send', 'event', 'webstart', 'detected', 'nojava');
        } else {
            //Java 7 detected, suggest upgrading or using older version
            //$("#versioninfo").text("Version-info: " + result.toString());
            $("#java7Dialog").dialog("open");
            //ga('send', 'event', 'webstart', 'detected', 'java7');
        }
    } else {
        //Java 8 detected, launch latest jFed version!
        dtjava.launch({url: url}, platform8, {});
        //ga('send', 'event', 'webstart', 'start', 'java8beta');
    }

    return false;
}
