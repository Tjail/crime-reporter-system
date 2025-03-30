function formatTags() {
    const elements = document.getElementsByClassName('body');
    for (let i = 0; i <elements.length; i++) {
        let bodyText = elements[i].children[0].innerText;

        let words = bodyText.split(' ');

        for (let j= 0; j < words.length; j++) {
            if (words[j][0] === '#') {
                let replacedText = bodyText.replace(/\s\#(.*?)(\s|$)/g, ` <a href="/social/explore?query=${words[j].substring(1)}">${words[j]}</a>` )
                elements[i].innerHTML = replacedText;
            }
        }
    }
}

formatTags();