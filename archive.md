---
layout: default
title: Archive
---

<div class="archive-content">
  <h1>Article Archive</h1>
  
  {% assign posts_by_year = site.posts | group_by_exp: "post", "post.date | date: '%Y'" %}
  
  {% for year in posts_by_year %}
    <div class="year-section">
      <h2>{{ year.name }}</h2>
      
      {% assign posts_by_month = year.items | group_by_exp: "post", "post.date | date: '%B'" %}
      
      {% for month in posts_by_month %}
        <div class="month-section">
          <h3>{{ month.name }}</h3>
          <ul class="post-list">
            {% for post in month.items %}
              <li>
                <span class="post-date">{{ post.date | date: "%d" }}</span>
                <a href="{{ post.url }}">{{ post.title }}</a>
              </li>
            {% endfor %}
          </ul>
        </div>
      {% endfor %}
    </div>
  {% endfor %}
</div>

<style>
.archive-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.archive-content h1 {
  color: #00ff00;
  margin-bottom: 2rem;
}

.year-section {
  margin-bottom: 3rem;
}

.year-section h2 {
  color: #00ff00;
  border-bottom: 1px solid #333;
  padding-bottom: 0.5rem;
  margin-bottom: 1.5rem;
}

.month-section {
  margin-bottom: 2rem;
}

.month-section h3 {
  color: #00ff00;
  margin-bottom: 1rem;
}

.post-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.post-list li {
  display: flex;
  align-items: baseline;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  border: 1px solid #333;
  transition: all 0.3s ease;
}

.post-list li:hover {
  background: #1a1a1a;
  border-color: #00ff00;
}

.post-date {
  color: #666;
  margin-right: 1rem;
  min-width: 2rem;
}

.post-list a {
  color: #fff;
  text-decoration: none;
}

.post-list a:hover {
  color: #00ff00;
}
</style> 