import { getCookie } from "./utils.js";
class Api
{
    #api_request(url, options = {}) {
        const method = options.method || "GET";

        // jQuery-style headers
        const headers = {
            "Content-Type": "application/json"
        };

        if (method !== "GET") {
            headers["X-CSRFToken"] = getCookie("csrftoken");
        }

        return $.ajax({
            url: url,
            method: method,
            headers: headers,
            data: options.body ? JSON.stringify(options.body) : null,
            dataType: "json",
            contentType: "application/json",
            error: function(xhr) {
                throw new Error(`${url}: ${xhr.status}`);
            }
        });
    }

    api(url,options={}) {
        return this.#api_request(url,options);
    }
}

export const API = new  Api();
