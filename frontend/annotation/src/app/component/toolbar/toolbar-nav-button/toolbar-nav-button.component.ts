import { Component, Input } from '@angular/core';

@Component({
    selector: 'app-toolbar-nav-button',
    templateUrl: './toolbar-nav-button.component.html',
    styleUrls: ['./toolbar-nav-button.component.scss']
})
export class ToolbarNavButtonComponent {
    @Input() icon;
    @Input() link;
}
