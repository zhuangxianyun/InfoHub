document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("search-input");
  const searchButton = document.getElementById("search-button");
  const aiCombineButton = document.getElementById("ai-combine-button");
  const searchResult = document.getElementById("search-result");

  function performSearch() {
    const searchTerm = searchInput.value;
    console.log("Performing search for:", searchTerm);
    searchResult.textContent = "正在搜索...";

    fetch("http://127.0.0.1:5000/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: searchTerm }),
    })
      .then((response) => {
        console.log("Response status:", response.status);
        return response.json();
      })
      .then((data) => {
        console.log("Received data:", data);
        if (data.error) {
          throw new Error(data.error);
        }
        displaySearchComplete();
      })
      .catch((error) => {
        console.error("Error:", error);
        searchResult.textContent =
          "搜索出错，请稍后再试。错误详情：" + error.message;
      });
  }

  function displaySearchComplete() {
    searchResult.textContent = "已经搜索到所需信息，请点击AI生成按键。";
  }

  function performAICombine() {
    console.log("Performing AI generation");
    searchResult.textContent = "正在执行 AI 生成操作...";

    // 首先执行 Combine 操作
    fetch("http://127.0.0.1:5000/combine", {
      method: "POST",
    })
      .then((response) => {
        console.log("Combine Response status:", response.status);
        if (!response.ok) {
          throw new Error(`Combine HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        console.log("Combine operation completed:", data);
        // 在 Combine 操作完成后，执行 AI 组合操作
        return fetch("http://127.0.0.1:5000/ai-combine", {
          method: "POST",
        });
      })
      .then((response) => {
        console.log("AI Combine Response status:", response.status);
        if (!response.ok) {
          throw new Error(`AI Combine HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        console.log("Received AI Combine data:", data);
        if (data.error) {
          throw new Error(data.error);
        }
        displayAISummary(data.result);
      })
      .catch((error) => {
        console.error("Error:", error);
        searchResult.textContent =
          "AI组合出错，请稍后再试。错误详情：" + (error.error || error.message);
      });
  }

  function displayAISummary(htmlContent) {
    searchResult.innerHTML =
      '<div class="ai-summary-container">' + htmlContent + "</div>";
    // 目录生成的代码已被完全移除
  }

  function displayResults(data) {
    console.log("Displaying results, data:", data);
    searchResult.innerHTML = "";

    if (data.processed_data && Array.isArray(data.processed_data.activities)) {
      data.processed_data.activities.forEach((item) => {
        const resultElement = document.createElement("div");
        resultElement.className = "result-card";
        resultElement.innerHTML = `
          <h3>${item.title || "无标题"}</h3>
          <p>${item.description || "无描述"}</p>
          ${
            item.url ? `<a href="${item.url}" target="_blank">查看详情</a>` : ""
          }
        `;
        searchResult.appendChild(resultElement);
      });
    } else {
      const resultElement = document.createElement("pre");
      resultElement.textContent = JSON.stringify(data.processed_data, null, 2);
      searchResult.appendChild(resultElement);
    }

    if (data.combined_notes_file) {
      const notesLink = document.createElement("p");
      notesLink.innerHTML = `所有笔记内容已保存到：<a href="${data.combined_notes_file}" target="_blank">${data.combined_notes_file}</a>`;
      searchResult.appendChild(notesLink);
    }
  }

  searchButton.addEventListener("click", performSearch);
  aiCombineButton.addEventListener("click", performAICombine);
  searchInput.addEventListener("keyup", function (event) {
    if (event.key === "Enter") {
      performSearch();
    }
  });
});
