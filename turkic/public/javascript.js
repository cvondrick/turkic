function mturk_parameters()
{
    var retval = new Object();

    if (window.location.href.indexOf("?") == -1)
    {
        retval.assignmentid = null;
        retval.hitid = null;
        retval.workerid = null;
        retval.action = null;
        return retval;
    }

    var params = window.location.href.split("?")[1].split("&");

    for (var i in params)
    {
        var sp = params[i].split("=");
        if (sp.length <= 1)
        {
            continue;
        }
        var result = sp[1].split("#")[0];

        if (sp[0] == "assignmentId")
        {
            retval.assignmentid = result;
        }
        else if (sp[0] == "hitId")
        {
            retval.hitid = result;
        }
        else if (sp[0] == "workerId")
        {
            retval.workerid = result;
        }
        else if (sp[0] == "turkSubmitTo")
        {
            retval.action = decodeURIComponent(result) +
                "/mturk/externalSubmit";
        }
    }
    
    return retval;
}

function mturk_isassigned()
{
    var params = mturk_parameters();
    return params.assignmentid &&
        params.assignmentid != "ASSIGNMENT_ID_NOT_AVAILABLE" &&
        params.hitid && params.workerid;
}

function mturk_submit()
{
    if (!mturk_isassigned())
    {
        alert("Cannot submit task because it is not accepted.");
        return;
    }

    var params = mturk_parameters();

    $("body").append('<form method="get" id="turkic_mturk">' +
        '<input type="hidden" name="assignmentId" value="">' +
        '</form>');

    $("#turkic_mturk input"].val(params.assignmentid);
    $("#turkic_mturk").attr("action", params.action);
    $("#turkic_mturk").submit();
}

function mturk_acceptfirst()
{
    var af = $('<div id="turkic_acceptfirst"></div>').prependTo("body")
    af.html("You must accept the HIT before you can continue.");
}

function worker_showstatistics()
{
    server_workerstatus(function(data) {
        var st = $('<div id="turkic_workerstatus"></div>');
        st.prependTo("body");

        var subm = $('<div class="turkic_workerstatusnumber"></div>');
        subm.html(data["numsubmitted"]);
        subm.appendTo(st);
        st.append("submitted");

        var accp = $('<div class="turkic_workerstatusnumber"></div>');
        accp.html(data["numaccepted"]);
        accp.appendTo(st);
        st.append("accepted");

        var rejt = $('<div class="turkic_workerstatusnumber"></div>');
        rejt.html(data["numrejected"]);
        rejt.appendTo(st);
        st.append("rejected");
    });
}

function worker_showtraining()
{
    var tr = $('<div id="turkic_training"></div>');
    tr.appendTo("body");
}

function worker_hidetraining()
{
    $("#turkic_training").remove();
}

function worker_needstraining(iftrue, iffalse = null)
{
    server_workerstatus(function(data) {
        if (data["trained"])
        {
            iftrue(data);
        }
        else if (iffalse != null)
        {
            iffalse(data);
        }
    });
}

function server_geturl(action, parameters)
{
    var url = "server/" + action;
    for (var x in parameters)
    {
        url += "/" + parameters[x];
    }
    return url;
}

function server_request(action, parameters, callback)
{
    $.ajax({
        url: server_geturl(action, parameters);
        dataType: "json",
        success: function(data) {
            callback(data);
        },
        error: function(xhr, textstatus) {
            document.write(xhr.responseText);
        }
    });
}

var server_workerstatus_data = null;
function server_workerstatus(callback)
{
    if (server_workerstatus_data == null)
    {
        var params = mturk_parameters();
        if (params.workerid)
        {
            server_request("turkic_getworkerstatus",
                {"workerid": params.workerid},
                function (data) {
                    server_workerstatus_data = data;
                    callback(data);
                });
        }
    }
    else
    {
        callback(server_workerstatus_data);
    }
}
