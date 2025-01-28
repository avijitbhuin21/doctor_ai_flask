document.addEventListener('DOMContentLoaded', () => {
    // Smooth scroll handling for containers
    const scrollContainers = document.querySelectorAll('[data-scroll-container]');
    
    scrollContainers.forEach(container => {
        let isDown = false;
        let startX;
        let scrollLeft;

        container.addEventListener('mousedown', (e) => {
            isDown = true;
            container.style.cursor = 'pointer';
            startX = e.pageX - container.offsetLeft;
            scrollLeft = container.scrollLeft;
        });

        container.addEventListener('mouseleave', () => {
            isDown = false;
            container.style.cursor = 'pointer';
        });

        container.addEventListener('mouseup', () => {
            isDown = false;
            container.style.cursor = 'pointer';
        });

        container.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - container.offsetLeft;
            const walk = (x - startX) * 2;
            container.scrollLeft = scrollLeft - walk;
        });

        // Add grab cursor by default
        container.style.cursor = 'pointer';

        // Handle wheel scrolling
        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            container.scrollLeft += e.deltaY;
        });
    });

    // Add hover effect for boxes
    const boxes = document.querySelectorAll('.box');
    
    boxes.forEach(box => {
        box.addEventListener('mousemove', (e) => {
            const rect = box.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            box.style.setProperty('--mouse-x', `${x}px`);
            box.style.setProperty('--mouse-y', `${y}px`);
        });
    });
});
