var href = "https://www.liepin.com/zhaopin/?city=410&dq=410&pubTime=&currentPage=5&pageSize=40&key=%E9%80%89%E5%9D%80%E5%BC%80%E5%8F%91&suggestTag=&workYearCode=&compId=&compName=&compTag=&industry=H12$H0095&salaryCode=&jobKind=2&compScale=&compKind=&compStage=&eduLevel=&otherCity=&sfrom=search_job_pc&ckId=bha8gfm4xcur4bhwxoc0wrp939qulhxb&scene=page&skId=ev6asjzncukfw4wk084yixpas6q9k4qa&fkId=m75oa0dved7921l19o0t17j0zavnzs59&suggestId=";
uuidV4 = function() {
                var r = (new Date).getTime()
                  , n = "undefined" != typeof performance && performance.now && 1e3 * performance.now() || 0;
                return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function(o) {
                    var i = 16 * Math.random();
                    return r > 0 ? (i = Math.floor((r + i) % 16),
                    r = Math.floor(r / 16)) : (i = Math.floor((n + i) % 16),
                    n = Math.floor(n / 16)),
                    ("x" === o ? i : i / 4 + 8).toString(16)
                })
            }
function W() {
            var e = arguments.length > 0 && void 0 !== arguments[0] ? arguments[0] : 8
              , t = (new Date).getTime()
              , n = new Array(e < 8 ? 8 : e).join("x");
            return "".concat(n, "y").replace(/[xy]/g, (function(e) {
                var n = (t + 36 * Math.random()) % 36 | 0;
                return t = Math.floor(t / 36),
                ("x" === e ? n : 3 & n | 8).toString(36)
            }
            ))
        }
var E = function(e, t) {
            var n = t || String(href);
            -1 !== n.indexOf("#") && (n = n.substring(0, n.indexOf("#")));
            for (var r, o = [], i = new RegExp("(^|\\?|&)" + e + "=([^&]*)(?=&|#|$)","g"); null !== (r = i.exec(n)); )
                try {
                    o.push(decodeURIComponent(r[2]))
                } catch (a) {
                    console.error(a)
                }
            return 0 === o.length ? null : 1 === o.length ? o[0] : o
        };
var x = function (e) {
    var t = (0,
        E)(e);
    return Array.isArray(t) ? t[0] : t
};
function get_passThroughForm(){
    var passThroughForm = {
        scene: x("scene") || p.Rf.Init,
        skId: x("skId") || "",
        fkId: x("fkId") || "",
        ckId: W(32),
        sfrom: "search_job_pc"
    };
    return passThroughForm;
}
function getHeadersId(){
    return uuidV4();
}
console.log(get_passThroughForm());
console.log(getHeadersId());