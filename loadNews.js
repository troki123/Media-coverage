async function loadNews() 
{
    const query = document.getElementById("query").value;
    const articlesDiv = document.getElementById("articles");


    try {
        // comunicates with program.py and turns the python code into js code
        const res = await fetch(`http://127.0.0.1:5000/news-summary?q=${query}`);
        const data = await res.json();

        // shows articles under div with articles id
        articlesDiv.innerHTML = "<h2>Articles</h2>";

        data.articles.forEach(article => {
            const div = document.createElement("div");
            div.innerHTML = `<a href="${article.url}" target="_blank">${article.title}</a>`;
            articlesDiv.appendChild(div);
        });

    } 
    catch (error) {
        articlesDiv.innerHTML = "<p>Error loading news</p>";
        console.error(error);
    }
}