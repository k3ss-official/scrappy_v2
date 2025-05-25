"""
Format Converter Module for Scrappy

This module handles the conversion of scraped data into various output formats.
"""

import os
import json
import csv
import logging
import yaml
import xml.dom.minidom
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scrappy.formatters')

class FormatConverter:
    """
    Converter for transforming scraped data into various output formats.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize the format converter.
        
        Args:
            output_dir: Directory to save converted output
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Initialized format converter with output directory: {output_dir}")
    
    def convert(self, data: Dict[str, Any], formats: List[str], base_filename: str) -> Dict[str, str]:
        """
        Convert data to specified formats.
        
        Args:
            data: Data to convert
            formats: List of output formats ('json', 'csv', 'txt', 'yaml', 'xml')
            base_filename: Base filename for output files (without extension)
            
        Returns:
            Dictionary mapping format to output file path
        """
        results = {}
        
        for fmt in formats:
            if fmt.lower() == 'json':
                output_path = self._convert_to_json(data, base_filename)
                results['json'] = output_path
            elif fmt.lower() == 'csv':
                output_path = self._convert_to_csv(data, base_filename)
                results['csv'] = output_path
            elif fmt.lower() == 'txt':
                output_path = self._convert_to_txt(data, base_filename)
                results['txt'] = output_path
            elif fmt.lower() == 'yaml':
                output_path = self._convert_to_yaml(data, base_filename)
                results['yaml'] = output_path
            elif fmt.lower() == 'xml':
                output_path = self._convert_to_xml(data, base_filename)
                results['xml'] = output_path
            else:
                logger.warning(f"Unsupported format: {fmt}")
        
        return results
    
    def _convert_to_json(self, data: Dict[str, Any], base_filename: str) -> str:
        """
        Convert data to JSON format.
        
        Args:
            data: Data to convert
            base_filename: Base filename for output file
            
        Returns:
            Path to the output file
        """
        output_path = os.path.join(self.output_dir, f"{base_filename}.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Data converted to JSON: {output_path}")
        return output_path
    
    def _convert_to_csv(self, data: Dict[str, Any], base_filename: str) -> str:
        """
        Convert data to CSV format.
        
        Args:
            data: Data to convert
            base_filename: Base filename for output file
            
        Returns:
            Path to the output file
        """
        output_path = os.path.join(self.output_dir, f"{base_filename}.csv")
        
        # Flatten nested data for CSV format
        flattened_data = self._flatten_data(data)
        
        # Write to CSV
        if flattened_data:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                writer.writeheader()
                writer.writerows(flattened_data)
        else:
            # If flattening failed, create a simple key-value CSV
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Key', 'Value'])
                for key, value in data.items():
                    if isinstance(value, (str, int, float, bool)):
                        writer.writerow([key, value])
                    else:
                        writer.writerow([key, str(value)])
        
        logger.info(f"Data converted to CSV: {output_path}")
        return output_path
    
    def _convert_to_txt(self, data: Dict[str, Any], base_filename: str) -> str:
        """
        Convert data to plain text format.
        
        Args:
            data: Data to convert
            base_filename: Base filename for output file
            
        Returns:
            Path to the output file
        """
        output_path = os.path.join(self.output_dir, f"{base_filename}.txt")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            self._write_dict_as_text(f, data)
        
        logger.info(f"Data converted to TXT: {output_path}")
        return output_path
    
    def _write_dict_as_text(self, file, data: Dict[str, Any], indent: int = 0):
        """
        Write dictionary as formatted text.
        
        Args:
            file: File object to write to
            data: Dictionary to write
            indent: Indentation level
        """
        for key, value in data.items():
            if isinstance(value, dict):
                file.write(f"{' ' * indent}{key}:\n")
                self._write_dict_as_text(file, value, indent + 2)
            elif isinstance(value, list):
                file.write(f"{' ' * indent}{key}:\n")
                for item in value:
                    if isinstance(item, dict):
                        file.write(f"{' ' * (indent + 2)}- \n")
                        self._write_dict_as_text(file, item, indent + 4)
                    else:
                        file.write(f"{' ' * (indent + 2)}- {item}\n")
            else:
                file.write(f"{' ' * indent}{key}: {value}\n")
    
    def _convert_to_yaml(self, data: Dict[str, Any], base_filename: str) -> str:
        """
        Convert data to YAML format.
        
        Args:
            data: Data to convert
            base_filename: Base filename for output file
            
        Returns:
            Path to the output file
        """
        output_path = os.path.join(self.output_dir, f"{base_filename}.yaml")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Data converted to YAML: {output_path}")
        return output_path
    
    def _convert_to_xml(self, data: Dict[str, Any], base_filename: str) -> str:
        """
        Convert data to XML format.
        
        Args:
            data: Data to convert
            base_filename: Base filename for output file
            
        Returns:
            Path to the output file
        """
        output_path = os.path.join(self.output_dir, f"{base_filename}.xml")
        
        # Create XML document
        doc = xml.dom.minidom.getDOMImplementation().createDocument(None, "root", None)
        root = doc.documentElement
        
        # Convert dictionary to XML
        self._dict_to_xml(doc, root, data)
        
        # Write to file with pretty formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(doc.toprettyxml(indent="  "))
        
        logger.info(f"Data converted to XML: {output_path}")
        return output_path
    
    def _dict_to_xml(self, doc, parent, data):
        """
        Convert dictionary to XML elements.
        
        Args:
            doc: XML document
            parent: Parent XML element
            data: Dictionary to convert
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    elem = doc.createElement(str(key))
                    parent.appendChild(elem)
                    self._dict_to_xml(doc, elem, value)
                else:
                    elem = doc.createElement(str(key))
                    parent.appendChild(elem)
                    text = doc.createTextNode(str(value))
                    elem.appendChild(text)
        elif isinstance(data, list):
            for item in data:
                elem = doc.createElement("item")
                parent.appendChild(elem)
                self._dict_to_xml(doc, elem, item)
        else:
            text = doc.createTextNode(str(data))
            parent.appendChild(text)
    
    def _flatten_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten nested data for CSV format.
        
        Args:
            data: Data to flatten
            
        Returns:
            List of flattened dictionaries
        """
        result = []
        
        # Try to identify list of items to convert to rows
        for key, value in data.items():
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                # Found a list of dictionaries, use this as rows
                return value
        
        # If no suitable list found, create a single row with flattened keys
        flat_dict = {}
        self._flatten_dict(data, flat_dict)
        result.append(flat_dict)
        
        return result
    
    def _flatten_dict(self, nested_dict: Dict[str, Any], flat_dict: Dict[str, Any], prefix: str = ''):
        """
        Flatten a nested dictionary.
        
        Args:
            nested_dict: Nested dictionary to flatten
            flat_dict: Output dictionary to store flattened keys
            prefix: Prefix for keys
        """
        for key, value in nested_dict.items():
            if isinstance(value, dict):
                self._flatten_dict(value, flat_dict, f"{prefix}{key}_")
            elif isinstance(value, list):
                # For lists, join values with commas
                if all(isinstance(item, (str, int, float, bool)) for item in value):
                    flat_dict[f"{prefix}{key}"] = ", ".join(str(item) for item in value)
                else:
                    flat_dict[f"{prefix}{key}"] = str(value)
            else:
                flat_dict[f"{prefix}{key}"] = value
